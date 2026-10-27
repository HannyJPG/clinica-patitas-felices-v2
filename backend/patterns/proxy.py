"""
PATRÓN PROXY (Estructural - GoF)
Puntos de sustentación: 1 y 4.
Propósito: Actuar como un guardián de seguridad (Protection Proxy) antes de llegar
al controlador real (RealClinicController). Verifica:
1) Que el token JWT sea auténtico y no haya expirado.
2) Que la sesión y el usuario existan en la Base de Datos con estado == 'activo'.
3) Que la estrategia RBAC del rol autorice la acción solicitada antes de ejecutar el controlador real.
"""

from abc import ABC, abstractmethod
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional

from .adapter import IDatabaseAdapter
from .strategy import RBACContext


class ErrorSeguridadProxy(PermissionError):
    """Excepción lanzada por AuthSessionProxy cuando el acceso es denegado."""

    def __init__(self, mensaje: str, codigo_http: int = 401) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_http = codigo_http


# =============================================================================
# UTILIDADES JWT NATIVAS (HS256 ESTÁNDAR RFC 7519 SIN DEPENDENCIAS FRÁGILES)
# =============================================================================

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(texto: str) -> bytes:
    padding = "=" * (-len(texto) % 4)
    return base64.urlsafe_b64decode((texto + padding).encode("ascii"))


def generar_token_jwt(payload: Dict[str, Any], duracion_segundos: int = 28800) -> str:
    """Genera un token JWT firmado con HMAC-SHA256."""
    secreto = os.getenv("JWT_SECRET", "patitas-felices-clave-secreta-2026").encode("utf-8")
    header = {"alg": "HS256", "typ": "JWT"}
    ahora = int(time.time())
    cuerpo = {
        **payload,
        "iat": ahora,
        "exp": ahora + duracion_segundos,
    }
    segmento_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    segmento_payload = _b64url_encode(json.dumps(cuerpo, separators=(",", ":")).encode("utf-8"))
    mensaje = f"{segmento_header}.{segmento_payload}".encode("ascii")
    firma = hmac.new(secreto, mensaje, hashlib.sha256).digest()
    return f"{segmento_header}.{segmento_payload}.{_b64url_encode(firma)}"


def verificar_token_jwt(token: str) -> Dict[str, Any]:
    """Verifica firma y vigencia de un token JWT HS256."""
    if not token or not isinstance(token, str):
        raise ErrorSeguridadProxy("Token JWT ausente. Inicie sesión para continuar.", 401)

    token_limpio = token.replace("Bearer ", "").strip()
    partes = token_limpio.split(".")
    if len(partes) != 3:
        raise ErrorSeguridadProxy("Formato de token JWT inválido.", 401)

    secreto = os.getenv("JWT_SECRET", "patitas-felices-clave-secreta-2026").encode("utf-8")
    mensaje = f"{partes[0]}.{partes[1]}".encode("ascii")
    firma_esperada = _b64url_encode(hmac.new(secreto, mensaje, hashlib.sha256).digest())

    if not hmac.compare_digest(firma_esperada, partes[2]):
        raise ErrorSeguridadProxy("Firma de token JWT inválida o adulterada.", 401)

    try:
        payload = json.loads(_b64url_decode(partes[1]).decode("utf-8"))
    except Exception as exc:
        raise ErrorSeguridadProxy("No se pudo decodificar el contenido del token JWT.", 401) from exc

    if int(payload.get("exp", 0)) < int(time.time()):
        raise ErrorSeguridadProxy("La sesión JWT ha expirado. Vuelva a iniciar sesión.", 401)

    return payload


# =============================================================================
# SUJETO E IMPLEMENTACIÓN DEL PATRÓN PROXY
# =============================================================================

class ISecureController(ABC):
    """Subject Interface: Contrato común entre el Controlador Real y el Proxy."""

    @abstractmethod
    def ejecutar_accion(
        self, token: Optional[str], accion: str, parametros: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        pass


class RealClinicController(ISecureController):
    """
    RealSubject (Controlador Real):
    Contiene las operaciones sensibles de la clínica (CRM, gestión de usuarios,
    agenda médica e historial clínico). Asume que quien lo invoca ya pasó por el Proxy.
    """

    def __init__(self, db_adapter: IDatabaseAdapter) -> None:
        self.db = db_adapter

    def ejecutar_accion(
        self, token: Optional[str], accion: str, parametros: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        params = parametros or {}
        usuario_actual = params.get("_usuario_autenticado", {})

        if accion == "ver_crm_dashboard":
            usuarios = self.db.listar_usuarios()
            ventas = self.db.listar_ventas()
            citas = self.db.listar_citas()
            productos = self.db.listar_productos(solo_activos=False)
            ingresos_totales = round(sum(float(v["total"]) for v in ventas), 2)
            return {
                "resumen": {
                    "total_usuarios": len(usuarios),
                    "usuarios_activos": sum(1 for u in usuarios if u["estado"] == "activo"),
                    "total_citas": len(citas),
                    "citas_pendientes": sum(1 for c in citas if c["estado"] == "pendiente"),
                    "total_ventas": len(ventas),
                    "ingresos_totales": ingresos_totales,
                    "stock_total_unidades": sum(int(p["stock"]) for p in productos),
                },
                "usuarios": usuarios,
                "ventas": ventas,
                "citas": citas,
                "productos": productos,
            }

        if accion == "cambiar_estado_usuario":
            usuario_id = int(params["usuario_id"])
            nuevo_estado = str(params["estado"]).lower()
            if nuevo_estado not in ("activo", "inactivo"):
                raise ValueError("El estado debe ser 'activo' o 'inactivo'.")
            actualizado = self.db.actualizar_estado_usuario(usuario_id, nuevo_estado)
            if not actualizado:
                raise LookupError(f"Usuario con ID {usuario_id} no encontrado.")
            return {"usuario": actualizado}

        if accion == "ver_agenda_doctor":
            citas = self.db.listar_citas()
            mascotas = self.db.listar_mascotas()
            return {"citas": citas, "mascotas": mascotas}

        if accion == "actualizar_diagnostico":
            cita_id = int(params["cita_id"])
            estado = str(params.get("estado", "atendida"))
            diagnostico = str(params.get("diagnostico", "")).strip()
            tratamiento = str(params.get("tratamiento", "")).strip()
            cita = self.db.actualizar_cita_doctor(
                cita_id=cita_id,
                estado=estado,
                diagnostico=diagnostico,
                tratamiento=tratamiento,
                doctor_id=usuario_actual.get("id"),
            )
            if not cita:
                raise LookupError(f"La cita #{cita_id} no existe.")
            return {"cita": cita}

        if accion == "agendar_cita":
            nueva_cita = self.db.crear_cita(
                {
                    **params,
                    "usuario_id": usuario_actual.get("id"),
                }
            )
            return {"cita": nueva_cita}

        if accion == "ver_mis_citas":
            citas = self.db.listar_citas(usuario_id=usuario_actual.get("id"))
            mascotas = self.db.listar_mascotas(usuario_id=usuario_actual.get("id"))
            return {"citas": citas, "mascotas": mascotas}

        raise ValueError(f"Acción no implementada en el controlador real: {accion}")


class AuthSessionProxy(ISecureController):
    """
    Protection Proxy (Guardián de Seguridad y Sesión):
    Intercepta todas las llamadas hacia RealClinicController.
    1. Valida el token JWT.
    2. Consulta en tiempo real a la BD si el usuario sigue 'activo' (si un Admin lo
       desactiva en el CRM, el Proxy bloquea su acceso de inmediato).
    3. Evalúa el permiso mediante RBACContext (Patrón Strategy).
    """

    def __init__(self, real_controller: RealClinicController, db_adapter: IDatabaseAdapter) -> None:
        self._real_controller = real_controller
        self._db = db_adapter

    def validar_sesion(self, token: Optional[str]) -> Dict[str, Any]:
        payload = verificar_token_jwt(token or "")
        usuario_id = int(payload.get("sub", 0))
        usuario_bd = self._db.obtener_usuario_por_id(usuario_id)

        if not usuario_bd:
            raise ErrorSeguridadProxy("El usuario de la sesión no existe en el sistema.", 401)

        if usuario_bd.get("estado") != "activo":
            raise ErrorSeguridadProxy(
                "Cuenta inactiva o suspendida. El Proxy de seguridad bloqueó el acceso.", 403
            )

        return usuario_bd

    def ejecutar_accion(
        self, token: Optional[str], accion: str, parametros: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        # Paso 1 y 2: Verificar JWT y estado activo en base de datos
        usuario_bd = self.validar_sesion(token)

        # Paso 3: Delegar en Strategy + RBAC la verificación del permiso según rol
        contexto_rbac = RBACContext(usuario_bd["rol"])
        if not contexto_rbac.autorizar(accion):
            raise ErrorSeguridadProxy(
                f"Acceso denegado por RBAC: el rol '{usuario_bd['rol']}' no tiene permiso para '{accion}'.",
                403,
            )

        # Paso 4: Pasar la solicitud al Controlador Real enriquecida con el usuario verificado
        parametros_seguros = dict(parametros or {})
        parametros_seguros["_usuario_autenticado"] = usuario_bd
        return self._real_controller.ejecutar_accion(token, accion, parametros_seguros)
