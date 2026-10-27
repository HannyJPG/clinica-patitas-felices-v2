"""
API RESTful en Python (FastAPI) - Clínica Veterinaria Patitas Felices
Integra los 4 patrones de diseño GoF:
1. Proxy (AuthSessionProxy): Seguridad JWT y verificación de sesión activa.
2. Strategy + RBAC (RBACContext): Autorización dinámica por rol (Admin, Doctor, Cliente).
3. Adapter (IDatabaseAdapter / WhatsAppAdapter): Desacoplamiento de BD y WhatsApp.
4. Facade (TiendaFacade): Checkout unificado (Stock + CRM + Boleta PDF en memoria).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .patterns import (
    AuthSessionProxy,
    ErrorProcesoVenta,
    ErrorSeguridadProxy,
    IDatabaseAdapter,
    RBACContext,
    RealClinicController,
    TiendaFacade,
    WhatsAppAdapter,
    generar_token_jwt,
    obtener_adaptador_bd,
)


# =============================================================================
# MODELOS PYDANTIC (ESQUEMAS PARA SWAGGER / OPENAPI)
# =============================================================================

class LoginRequest(BaseModel):
    email: str = Field(..., examples=["admin@patitasfelices.pe"])
    password: str = Field(..., examples=["admin123"])


class ItemCarritoRequest(BaseModel):
    producto_id: int = Field(..., examples=[1])
    cantidad: int = Field(..., ge=1, examples=[2])


class CheckoutRequest(BaseModel):
    cliente_nombre: str = Field(..., min_length=2, examples=["Lucía Fernández"])
    cliente_documento: str = Field(..., min_length=8, max_length=15, examples=["74859632"])
    metodo_pago: str = Field(default="Tarjeta / Yape", examples=["Yape / Plin"])
    items: List[ItemCarritoRequest]


class CitaRequest(BaseModel):
    propietario: str = Field(..., min_length=2, max_length=80, examples=["Lucía Fernández"])
    telefono: str = Field(..., min_length=9, max_length=20, examples=["912345678"])
    mascota_nombre: str = Field(..., min_length=1, max_length=60, examples=["Luna"])
    servicio: str = Field(..., examples=["consulta-general"])
    fecha: str = Field(..., examples=["2026-10-30"])
    hora: str = Field(..., examples=["10:30"])
    motivo: str = Field(..., min_length=10, max_length=1000, examples=["Control general y revisión de vacunas anuales."])


class ActualizarCitaDoctorRequest(BaseModel):
    estado: str = Field(..., examples=["atendida"])
    diagnostico: str = Field(default="", examples=["Paciente estable, sin fiebre."])
    tratamiento: str = Field(default="", examples=["Control en 15 días y dieta blanda."])


class CambiarEstadoUsuarioRequest(BaseModel):
    estado: str = Field(..., examples=["inactivo"])


# =============================================================================
# FÁBRICA DE APLICACIÓN FASTAPI
# =============================================================================

def crear_app(db_adapter: Optional[IDatabaseAdapter] = None) -> FastAPI:
    app = FastAPI(
        title="Clínica Veterinaria Patitas Felices - API RESTful",
        description=(
            "Backend en Python (FastAPI) conectado a Astro mediante fetch(). "
            "Implementa los 4 patrones GoF: Proxy, Strategy + RBAC, Adapter y Facade."
        ),
        version="2.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    adaptador_bd = db_adapter or obtener_adaptador_bd()
    adaptador_whatsapp = WhatsAppAdapter()
    controlador_real = RealClinicController(adaptador_bd)
    proxy_seguridad = AuthSessionProxy(controlador_real, adaptador_bd)
    tienda_facade = TiendaFacade(adaptador_bd, adaptador_whatsapp)

    app.state.db = adaptador_bd
    app.state.whatsapp = adaptador_whatsapp
    app.state.proxy = proxy_seguridad
    app.state.facade = tienda_facade

    def _manejar_proxy(token: Optional[str], accion: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            return proxy_seguridad.ejecutar_accion(token, accion, params)
        except ErrorSeguridadProxy as exc:
            raise HTTPException(status_code=exc.codigo_http, detail=exc.mensaje) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/health", tags=["Sistema"])
    def verificar_estado() -> Dict[str, Any]:
        return {
            "status": "ok",
            "clinica": "Patitas Felices",
            "patrones_activos": ["Proxy", "Strategy+RBAC", "Adapter", "Facade"],
            "adaptador_bd": type(adaptador_bd).__name__,
        }

    # -------------------------------------------------------------------------
    # 1. AUTENTICACIÓN Y SESIÓN (PATRÓN PROXY + STRATEGY RBAC)
    # -------------------------------------------------------------------------
    @app.post("/api/auth/login", tags=["Autenticación y RBAC (Proxy + Strategy)"])
    def iniciar_sesion(credenciales: LoginRequest) -> Dict[str, Any]:
        usuario = adaptador_bd.obtener_usuario_por_email(credenciales.email)
        if not usuario or usuario["password_hash"] != credenciales.password:
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

        if usuario["estado"] != "activo":
            raise HTTPException(
                status_code=403,
                detail="Cuenta inactiva o suspendida. El Proxy de seguridad bloqueó el inicio de sesión.",
            )

        # Patrón Strategy: Determinar vistas y permisos según el rol del usuario
        contexto_rbac = RBACContext(usuario["rol"])
        config_vista = contexto_rbac.obtener_vista_y_permisos()

        token = generar_token_jwt(
            {
                "sub": usuario["id"],
                "email": usuario["email"],
                "rol": usuario["rol"],
                "nombre": usuario["nombre"],
            }
        )

        return {
            "mensaje": f"Bienvenido(a), {usuario['nombre']}",
            "token": token,
            "usuario": {
                "id": usuario["id"],
                "nombre": usuario["nombre"],
                "email": usuario["email"],
                "rol": usuario["rol"],
                "estado": usuario["estado"],
                "telefono": usuario.get("telefono", ""),
            },
            "rbac": config_vista,
        }

    @app.get("/api/auth/perfil", tags=["Autenticación y RBAC (Proxy + Strategy)"])
    def obtener_perfil(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        try:
            usuario = proxy_seguridad.validar_sesion(authorization)
        except ErrorSeguridadProxy as exc:
            raise HTTPException(status_code=exc.codigo_http, detail=exc.mensaje) from exc

        contexto_rbac = RBACContext(usuario["rol"])
        return {
            "usuario": {
                "id": usuario["id"],
                "nombre": usuario["nombre"],
                "email": usuario["email"],
                "rol": usuario["rol"],
                "estado": usuario["estado"],
            },
            "rbac": contexto_rbac.obtener_vista_y_permisos(),
        }

    # -------------------------------------------------------------------------
    # 2. TIENDA Y CHECKOUT CON BOLETA PDF (PATRÓN FACADE + ADAPTER)
    # -------------------------------------------------------------------------
    @app.get("/api/productos", tags=["Tienda y Checkout (Facade)"])
    def listar_productos() -> Dict[str, Any]:
        productos = adaptador_bd.listar_productos(solo_activos=True)
        return {"productos": productos}

    @app.post("/api/tienda/checkout", tags=["Tienda y Checkout (Facade)"])
    def procesar_compra_tienda(
        pedido: CheckoutRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        # El Proxy verifica que la sesión esté activa y que el rol tenga permiso 'comprar_productos'
        try:
            usuario = proxy_seguridad.validar_sesion(authorization)
            rbac = RBACContext(usuario["rol"])
            if not rbac.autorizar("comprar_productos"):
                raise ErrorSeguridadProxy(
                    f"El rol '{usuario['rol']}' no está autorizado para realizar compras.", 403
                )
        except ErrorSeguridadProxy as exc:
            raise HTTPException(status_code=exc.codigo_http, detail=exc.mensaje) from exc

        try:
            resultado = tienda_facade.procesar_venta(
                usuario_id=usuario["id"],
                cliente_nombre=pedido.cliente_nombre,
                cliente_documento=pedido.cliente_documento,
                items=[item.model_dump() for item in pedido.items],
                metodo_pago=pedido.metodo_pago,
            )
            return {
                "mensaje": "Venta procesada exitosamente mediante TiendaFacade.",
                **resultado,
            }
        except ErrorProcesoVenta as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/tienda/boleta/{venta_id}/pdf", tags=["Tienda y Checkout (Facade)"])
    def descargar_boleta_pdf(venta_id: int) -> Response:
        ventas = adaptador_bd.listar_ventas()
        venta = next((v for v in ventas if int(v["id"]) == venta_id), None)
        if not venta:
            raise HTTPException(status_code=404, detail="Boleta no encontrada.")
        pdf_bytes = tienda_facade.pdf_generator.construir_pdf_en_memoria(venta)
        nombre_archivo = f"Boleta_{venta['numero_boleta']}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{nombre_archivo}"'},
        )

    # -------------------------------------------------------------------------
    # 3. CITAS Y ADAPTADOR WHATSAPP (PATRÓN ADAPTER + PROXY)
    # -------------------------------------------------------------------------
    @app.post("/api/citas", tags=["Citas y WhatsApp (Adapter)"])
    def registrar_cita(
        solicitud: CitaRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        datos = solicitud.model_dump()
        whatsapp_url = adaptador_whatsapp.generar_enlace_cita(datos)
        datos["whatsapp_url"] = whatsapp_url

        if authorization:
            resultado = _manejar_proxy(authorization, "agendar_cita", datos)
            cita = resultado["cita"]
        else:
            cita = adaptador_bd.crear_cita(datos)

        return {
            "mensaje": "Cita registrada y adaptada para WhatsApp exitosamente.",
            "cita": cita,
            "whatsapp_url": whatsapp_url,
        }

    @app.get("/api/cliente/mis-citas", tags=["Citas y WhatsApp (Adapter)"])
    def obtener_mis_citas(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        return _manejar_proxy(authorization, "ver_mis_citas")

    # -------------------------------------------------------------------------
    # 4. AGENDA E HISTORIAL DEL DOCTOR (PATRÓN PROXY + STRATEGY DOCTOR/ADMIN)
    # -------------------------------------------------------------------------
    @app.get("/api/doctor/agenda", tags=["Agenda e Historial (Doctor)"])
    def ver_agenda_doctor(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        return _manejar_proxy(authorization, "ver_agenda_doctor")

    @app.patch("/api/doctor/citas/{cita_id}", tags=["Agenda e Historial (Doctor)"])
    def actualizar_cita_clinica(
        cita_id: int,
        cuerpo: ActualizarCitaDoctorRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        return _manejar_proxy(
            authorization,
            "actualizar_diagnostico",
            {
                "cita_id": cita_id,
                "estado": cuerpo.estado,
                "diagnostico": cuerpo.diagnostico,
                "tratamiento": cuerpo.tratamiento,
            },
        )

    # -------------------------------------------------------------------------
    # 5. CRM Y DASHBOARD ADMINISTRATIVO (PATRÓN PROXY + STRATEGY ADMIN)
    # -------------------------------------------------------------------------
    @app.get("/api/admin/crm", tags=["CRM y Dashboard (Admin)"])
    def ver_crm_admin(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        return _manejar_proxy(authorization, "ver_crm_dashboard")

    @app.patch("/api/admin/usuarios/{usuario_id}/estado", tags=["CRM y Dashboard (Admin)"])
    def cambiar_estado_usuario(
        usuario_id: int,
        cuerpo: CambiarEstadoUsuarioRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        return _manejar_proxy(
            authorization,
            "cambiar_estado_usuario",
            {"usuario_id": usuario_id, "estado": cuerpo.estado},
        )

    # -------------------------------------------------------------------------
    # 6. VISOR EN VIVO DE LAS 16 TABLAS DE LA BASE DE DATOS (prueba_1.erd.json)
    # -------------------------------------------------------------------------
    @app.get("/api/bd/tablas", tags=["Base de Datos (16 Tablas prueba_1.erd.json)"])
    def consultar_todas_las_tablas() -> Dict[str, Any]:
        tablas_16 = adaptador_bd.obtener_todas_las_16_tablas()
        return {
            "motor": type(adaptador_bd).__name__,
            "archivo_sqlite": getattr(adaptador_bd, "db_path", "N/A"),
            "total_tablas": len(tablas_16),
            "tablas": tablas_16,
        }

    @app.get("/visor-bd", tags=["Base de Datos (16 Tablas prueba_1.erd.json)"])
    def visor_html_base_de_datos() -> Response:
        html = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Visor de 16 Tablas (prueba_1.erd.json) | Clínica Patitas Felices</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #f3eeea; color: #333; margin: 0; padding: 1.5rem; }
    .wrap { max-width: 1280px; margin: 0 auto; }
    header { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem; background: #fff7f0; padding: 1.25rem 1.5rem; border-radius: 14px; border: 1px solid #d9d0c5; margin-bottom: 1rem; }
    h1 { margin: 0; font-size: 1.45rem; color: #4e453b; }
    .meta { font-size: 0.9rem; color: #5e554a; margin-top: 0.25rem; }
    .btn { background: #776b5d; color: #fff; border: none; padding: 0.6rem 1rem; border-radius: 8px; font-weight: 600; cursor: pointer; text-decoration: none; font-size: 0.88rem; }
    .btn:hover { background: #5c5146; }
    .filtros { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-bottom: 1.25rem; }
    .chip { background: #ebe3d5; color: #4e453b; border: 1px solid #b0a695; padding: 0.35rem 0.75rem; border-radius: 999px; font-size: 0.82rem; font-weight: 600; cursor: pointer; }
    .chip.active { background: #776b5d; color: #fff; border-color: #776b5d; }
    .card { background: #fff7f0; border: 1px solid #d9d0c5; border-radius: 14px; padding: 1.15rem; margin-bottom: 1rem; overflow-x: auto; }
    h2 { margin-top: 0; font-size: 1.1rem; color: #4e453b; display: flex; justify-content: space-between; align-items: center; }
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; background: #fff; }
    th, td { border: 1px solid #d9d0c5; padding: 0.5rem 0.7rem; text-align: left; }
    th { background: #ebe3d5; color: #4e453b; }
    .empty { color: #5e554a; font-style: italic; margin: 0; }
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div>
        <h1>Visor en Vivo de las 16 Tablas (Integrado con prueba_1.erd.json)</h1>
        <div class="meta" id="meta-bd">Cargando las 16 tablas del modelo Entidad-Relación...</div>
      </div>
      <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
        <button class="btn" onclick="cargarTablas()">Actualizar en vivo</button>
        <a class="btn" href="/admin">Volver al CRM</a>
      </div>
    </header>
    <div class="filtros" id="barra-filtros"></div>
    <div id="contenedor"></div>
  </div>
  <script>
    let cacheTablas = {};
    let tablaSeleccionada = 'TODAS';

    function renderizar() {
      const cont = document.getElementById('contenedor');
      cont.innerHTML = '';
      for (const [nombre, filas] of Object.entries(cacheTablas)) {
        if (tablaSeleccionada !== 'TODAS' && tablaSeleccionada !== nombre) continue;
        const section = document.createElement('section');
        section.className = 'card';
        const h2 = document.createElement('h2');
        h2.innerHTML = '<span>Tabla: <code>' + nombre + '</code></span><span>' + filas.length + ' registro(s)</span>';
        section.appendChild(h2);
        if (!filas.length) {
          const p = document.createElement('p');
          p.className = 'empty';
          p.textContent = 'Sin registros todavía (realiza una compra en /tienda para poblar detalle_ventas).';
          section.appendChild(p);
        } else {
          const table = document.createElement('table');
          const cols = Object.keys(filas[0]);
          const thead = document.createElement('thead');
          const trh = document.createElement('tr');
          cols.forEach(c => { const th = document.createElement('th'); th.textContent = c; trh.appendChild(th); });
          thead.appendChild(trh);
          table.appendChild(thead);
          const tbody = document.createElement('tbody');
          filas.forEach(f => {
            const tr = document.createElement('tr');
            cols.forEach(c => { const td = document.createElement('td'); td.textContent = f[c] ?? ''; tr.appendChild(td); });
            tbody.appendChild(tr);
          });
          table.appendChild(tbody);
          section.appendChild(table);
        }
        cont.appendChild(section);
      }
    }

    async function cargarTablas() {
      const res = await fetch('/api/bd/tablas');
      const data = await res.json();
      cacheTablas = data.tablas || {};
      document.getElementById('meta-bd').textContent =
        'Total tablas activas: ' + data.total_tablas + ' | Adaptador: ' + data.motor + ' | BD: ' + data.archivo_sqlite;

      const filtros = document.getElementById('barra-filtros');
      filtros.innerHTML = '';
      const btnTodas = document.createElement('button');
      btnTodas.className = 'chip' + (tablaSeleccionada === 'TODAS' ? ' active' : '');
      btnTodas.textContent = 'Mostrar las 16 tablas';
      btnTodas.onclick = () => { tablaSeleccionada = 'TODAS'; cargarTablas(); };
      filtros.appendChild(btnTodas);

      Object.keys(cacheTablas).forEach((nom, idx) => {
        const b = document.createElement('button');
        b.className = 'chip' + (tablaSeleccionada === nom ? ' active' : '');
        b.textContent = (idx + 1) + '. ' + nom + ' (' + cacheTablas[nom].length + ')';
        b.onclick = () => { tablaSeleccionada = nom; cargarTablas(); };
        filtros.appendChild(b);
      });

      renderizar();
    }
    cargarTablas();
  </script>
</body>
</html>"""
        return Response(content=html, media_type="text/html")

    # Servir el Frontend compilado de Astro (dist/) en el mismo puerto para Hosting Unificado y Modo App
    dist_dir = Path(__file__).resolve().parent.parent / "dist"
    if dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="astro_frontend")

    return app


app = crear_app()
