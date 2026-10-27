"""
Pruebas Unitarias y de Integración con Pytest - Clínica Veterinaria Patitas Felices
Valida:
1. Cálculo de boletas, descuento de stock y PDF en memoria (Patrón Facade).
2. Permisos por rol RBAC y vistas dinámicas (Patrón Strategy).
3. Guardián de seguridad JWT y bloqueo de usuarios inactivos (Patrón Proxy).
4. Formateo de URL de WhatsApp y persistencia desacoplada (Patrón Adapter).
5. Endpoints RESTful de FastAPI.
"""

import base64
import pytest
from fastapi.testclient import TestClient

from backend.main import crear_app
from backend.patterns import (
    AdminRoleStrategy,
    AuthSessionProxy,
    ClientRoleStrategy,
    DoctorRoleStrategy,
    ErrorProcesoVenta,
    ErrorSeguridadProxy,
    RBACContext,
    RealClinicController,
    SQLiteDatabaseAdapter,
    SubsistemaCRMTransacciones,
    TiendaFacade,
    WhatsAppAdapter,
    generar_token_jwt,
)


@pytest.fixture()
def db_memoria() -> SQLiteDatabaseAdapter:
    """Base de datos SQLite en memoria aislada por cada prueba."""
    return SQLiteDatabaseAdapter(":memory:")


@pytest.fixture()
def client(db_memoria: SQLiteDatabaseAdapter) -> TestClient:
    """Cliente de pruebas FastAPI conectado al adaptador en memoria."""
    app = crear_app(db_adapter=db_memoria)
    return TestClient(app)


# =============================================================================
# 1. PRUEBAS DEL PATRÓN FACADE (CÁLCULO DE BOLETAS, STOCK Y PDF EN MEMORIA)
# =============================================================================

def test_calculo_exacto_boleta_igv() -> None:
    items = [
        {"producto_id": 1, "cantidad": 2, "precio_unitario": 59.00, "subtotal": 118.00},
    ]
    totales = SubsistemaCRMTransacciones.calcular_totales_boleta(items)
    assert totales["total"] == 118.00
    assert totales["subtotal"] == 100.00
    assert totales["igv"] == 18.00


def test_tienda_facade_procesa_venta_descuenta_stock_y_genera_pdf(db_memoria: SQLiteDatabaseAdapter) -> None:
    facade = TiendaFacade(db_memoria)
    producto_inicial = db_memoria.obtener_producto(1)
    assert producto_inicial is not None
    stock_antes = producto_inicial["stock"]

    resultado = facade.procesar_venta(
        usuario_id=3,
        cliente_nombre="Lucía Fernández",
        cliente_documento="74859632",
        items=[{"producto_id": 1, "cantidad": 2}],
        metodo_pago="Yape",
    )

    # 1. Verifica registro CRM y numeración de boleta
    venta = resultado["venta"]
    assert venta["numero_boleta"] == "B001-000001"
    assert venta["total"] == 290.00  # 2 * 145.00
    assert round(venta["subtotal"] + venta["igv"], 2) == 290.00

    # 2. Verifica descuento de stock en la BD
    producto_despues = db_memoria.obtener_producto(1)
    assert producto_despues is not None
    assert producto_despues["stock"] == stock_antes - 2

    # 3. Verifica construcción del archivo PDF real en memoria
    pdf_bytes = base64.b64decode(resultado["pdf_base64"])
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"CLINICA VETERINARIA PATITAS FELICES" in pdf_bytes
    assert b"B001-000001" in pdf_bytes


def test_tienda_facade_rechaza_venta_sin_stock(db_memoria: SQLiteDatabaseAdapter) -> None:
    facade = TiendaFacade(db_memoria)
    with pytest.raises(ErrorProcesoVenta, match="Stock insuficiente"):
        facade.procesar_venta(
            usuario_id=3,
            cliente_nombre="Lucía Fernández",
            cliente_documento="74859632",
            items=[{"producto_id": 1, "cantidad": 999}],
        )


# =============================================================================
# 2. PRUEBAS DEL PATRÓN STRATEGY + RBAC (PERMISOS POR STAKEHOLDER)
# =============================================================================

def test_rbac_strategies_permisos_y_vistas() -> None:
    contexto = RBACContext("cliente")
    assert contexto.autorizar("comprar_productos") is True
    assert contexto.autorizar("agendar_cita") is True
    assert contexto.autorizar("ver_crm_dashboard") is False
    assert contexto.autorizar("actualizar_diagnostico") is False
    assert contexto.obtener_vista_y_permisos()["ruta_principal"] == "/tienda"

    # Cambio dinámico de estrategia a Doctor
    contexto.cambiar_estrategia(DoctorRoleStrategy())
    assert contexto.autorizar("ver_agenda_doctor") is True
    assert contexto.autorizar("actualizar_diagnostico") is True
    assert contexto.autorizar("cambiar_estado_usuario") is False
    assert contexto.obtener_vista_y_permisos()["ruta_principal"] == "/doctor"

    # Cambio dinámico de estrategia a Admin
    contexto.cambiar_estrategia(AdminRoleStrategy())
    assert contexto.autorizar("ver_crm_dashboard") is True
    assert contexto.autorizar("cambiar_estado_usuario") is True
    assert contexto.obtener_vista_y_permisos()["ruta_principal"] == "/admin"


# =============================================================================
# 3. PRUEBAS DEL PATRÓN PROXY (GUARDIÁN DE SESIÓN JWT Y USUARIOS ACTIVOS)
# =============================================================================

def test_proxy_bloquea_token_ausente_y_usuario_inactivo(db_memoria: SQLiteDatabaseAdapter) -> None:
    controlador = RealClinicController(db_memoria)
    proxy = AuthSessionProxy(controlador, db_memoria)

    # Sin token -> 401
    with pytest.raises(ErrorSeguridadProxy) as exc_sin_token:
        proxy.ejecutar_accion(None, "ver_crm_dashboard")
    assert exc_sin_token.value.codigo_http == 401

    # Usuario 4 está 'inactivo' en el seed -> 403 aunque tenga JWT válido
    token_inactivo = generar_token_jwt({"sub": 4, "rol": "cliente"})
    with pytest.raises(ErrorSeguridadProxy, match="inactiva") as exc_inactivo:
        proxy.ejecutar_accion(token_inactivo, "ver_mis_citas")
    assert exc_inactivo.value.codigo_http == 403

    # Cliente activo intentando entrar al CRM de Admin -> 403 por RBAC
    token_cliente = generar_token_jwt({"sub": 3, "rol": "cliente"})
    with pytest.raises(ErrorSeguridadProxy, match="Acceso denegado por RBAC") as exc_rbac:
        proxy.ejecutar_accion(token_cliente, "ver_crm_dashboard")
    assert exc_rbac.value.codigo_http == 403

    # Admin activo accediendo al CRM -> permitido
    token_admin = generar_token_jwt({"sub": 1, "rol": "admin"})
    respuesta = proxy.ejecutar_accion(token_admin, "ver_crm_dashboard")
    assert "resumen" in respuesta
    assert respuesta["resumen"]["total_usuarios"] >= 4


# =============================================================================
# 4. PRUEBAS DEL PATRÓN ADAPTER (WHATSAPP URL Y BASE DE DATOS)
# =============================================================================

def test_whatsapp_adapter_formatea_url_correctamente() -> None:
    adapter = WhatsAppAdapter("51990853697")
    url = adapter.generar_enlace_cita(
        {
            "propietario": "Lucía Fernández",
            "telefono": "912345678",
            "mascota_nombre": "Luna",
            "servicio": "vacunacion",
            "fecha": "2026-11-05",
            "hora": "09:30",
            "motivo": "Refuerzo anual de vacuna séxtuple.",
        }
    )
    assert url.startswith("https://wa.me/51990853697?text=")
    assert "Luna" in url
    assert "05%2F11%2F2026" in url


# =============================================================================
# 5. PRUEBAS INTEGRALES DE ENDPOINTS FASTAPI (LOGIN, CHECKOUT, AGENDA Y CRM)
# =============================================================================

def test_flujo_completo_endpoints_fastapi(client: TestClient) -> None:
    # 1. Login como Cliente
    res_login = client.post(
        "/api/auth/login",
        json={"email": "cliente@patitasfelices.pe", "password": "cliente123"},
    )
    assert res_login.status_code == 200
    datos_cliente = res_login.json()
    token_cliente = datos_cliente["token"]
    assert datos_cliente["rbac"]["ruta_principal"] == "/tienda"

    # 2. Compra en tienda y descarga de PDF
    res_compra = client.post(
        "/api/tienda/checkout",
        headers={"Authorization": f"Bearer {token_cliente}"},
        json={
            "cliente_nombre": "Lucía Fernández",
            "cliente_documento": "74859632",
            "metodo_pago": "Yape",
            "items": [{"producto_id": 3, "cantidad": 2}],
        },
    )
    assert res_compra.status_code == 200
    venta_id = res_compra.json()["venta"]["id"]

    res_pdf = client.get(f"/api/tienda/boleta/{venta_id}/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-1.4")

    # 3. Login como Doctor y actualización de diagnóstico
    res_doc = client.post(
        "/api/auth/login",
        json={"email": "doctor@patitasfelices.pe", "password": "doctor123"},
    )
    token_doctor = res_doc.json()["token"]
    res_diag = client.patch(
        "/api/doctor/citas/1",
        headers={"Authorization": f"Bearer {token_doctor}"},
        json={
            "estado": "atendida",
            "diagnostico": "Paciente completamente recuperado.",
            "tratamiento": "Alta médica.",
        },
    )
    assert res_diag.status_code == 200
    assert res_diag.json()["cita"]["estado"] == "atendida"

    # 4. Login como Admin y desactivación de usuario para probar el Proxy en vivo
    res_admin = client.post(
        "/api/auth/login",
        json={"email": "admin@patitasfelices.pe", "password": "admin123"},
    )
    token_admin = res_admin.json()["token"]
    res_inactivar = client.patch(
        "/api/admin/usuarios/3/estado",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"estado": "inactivo"},
    )
    assert res_inactivar.status_code == 200
    assert res_inactivar.json()["usuario"]["estado"] == "inactivo"

    # Ahora el token anterior del cliente 3 es bloqueado inmediatamente por AuthSessionProxy
    res_bloqueado = client.get(
        "/api/cliente/mis-citas",
        headers={"Authorization": f"Bearer {token_cliente}"},
    )
    assert res_bloqueado.status_code == 403

    # 5. Visor en vivo de las 16 tablas de la Base de Datos (prueba_1.erd.json)
    res_tablas = client.get("/api/bd/tablas")
    assert res_tablas.status_code == 200
    cuerpo_tablas = res_tablas.json()
    assert cuerpo_tablas["total_tablas"] == 16
    tablas = cuerpo_tablas["tablas"]
    for nombre_tabla in (
        "Dueno",
        "Especie",
        "Razas",
        "Paciente",
        "Especialidad",
        "Veterinario",
        "Servicios",
        "Cita",
        "Detalle_servicios",
        "Historial_clinico",
        "Receta",
        "Factura",
        "Pago",
        "usuarios",
        "productos",
        "detalle_ventas",
    ):
        assert nombre_tabla in tablas
        assert len(tablas[nombre_tabla]) >= 1

    res_visor = client.get("/visor-bd")
    assert res_visor.status_code == 200
    assert "Visor en Vivo de las 16 Tablas" in res_visor.text
