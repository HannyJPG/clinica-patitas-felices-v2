import { API_BASE_URL, peticionApi, obtenerSesion, guardarSesion } from "./api-client.js";

(() => {
    const tablaUsuarios = document.getElementById("tabla-usuarios-crm");
    if (!tablaUsuarios) return;

    const estadoProxyAdmin = document.getElementById("estado-proxy-admin");
    const kpiIngresos = document.getElementById("kpi-ingresos");
    const kpiVentas = document.getElementById("kpi-ventas");
    const kpiUsuarios = document.getElementById("kpi-usuarios");
    const kpiStock = document.getElementById("kpi-stock");
    const tablaVentas = document.getElementById("tabla-ventas-crm");
    const listaInventario = document.getElementById("lista-inventario-crm");
    const btnRefrescar = document.getElementById("btn-refrescar-crm");

    async function asegurarSesionAdminParaDemo() {
        const sesion = obtenerSesion();
        if (sesion?.token && sesion?.usuario?.rol === "admin") {
            return sesion;
        }
        const loginAdmin = await peticionApi("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({
                email: "admin@patitasfelices.pe",
                password: "admin123"
            })
        });
        guardarSesion(loginAdmin);
        return loginAdmin;
    }

    function renderizarUsuarios(usuarios) {
        tablaUsuarios.replaceChildren();
        for (const u of usuarios) {
            const fila = document.createElement("div");
            fila.className = "p-3 border rounded bg-white d-flex flex-wrap justify-content-between align-items-center gap-2";

            const texto = document.createElement("div");
            const nombre = document.createElement("strong");
            nombre.className = "d-block";
            nombre.textContent = `${u.nombre} (${u.rol.toUpperCase()})`;
            const correo = document.createElement("span");
            correo.className = "small-note";
            correo.textContent = `${u.email} · Estado: ${u.estado.toUpperCase()}`;
            texto.append(nombre, correo);

            const btnEstado = document.createElement("button");
            btnEstado.type = "button";
            btnEstado.className = u.estado === "activo" ? "btn btn-outline-primary btn-sm" : "btn btn-primary btn-sm";
            const siguienteEstado = u.estado === "activo" ? "inactivo" : "activo";
            btnEstado.textContent = u.estado === "activo" ? "Suspender (Inactivar)" : "Reactivar cuenta";
            btnEstado.addEventListener("click", async () => {
                btnEstado.disabled = true;
                try {
                    await asegurarSesionAdminParaDemo();
                    await peticionApi(`/api/admin/usuarios/${u.id}/estado`, {
                        method: "PATCH",
                        body: JSON.stringify({ estado: siguienteEstado })
                    });
                    await cargarCrm();
                } finally {
                    btnEstado.disabled = false;
                }
            });

            fila.append(texto, btnEstado);
            tablaUsuarios.append(fila);
        }
    }

    function renderizarVentas(ventas) {
        tablaVentas.replaceChildren();
        if (!ventas.length) {
            const p = document.createElement("p");
            p.className = "small-note mb-0";
            p.textContent = "Aún no hay boletas emitidas. Realiza una compra en /tienda para ver cómo TiendaFacade la registra aquí.";
            tablaVentas.append(p);
            return;
        }

        for (const v of ventas) {
            const card = document.createElement("div");
            card.className = "p-3 border rounded bg-white d-flex flex-wrap justify-content-between align-items-center gap-2";

            const info = document.createElement("div");
            const titulo = document.createElement("strong");
            titulo.className = "d-block";
            titulo.textContent = `Boleta ${v.numero_boleta} · S/ ${Number(v.total).toFixed(2)} (IGV: S/ ${Number(v.igv).toFixed(2)})`;
            const sub = document.createElement("span");
            sub.className = "small-note";
            sub.textContent = `Cliente: ${v.cliente_nombre} (Doc: ${v.cliente_documento}) · Pago: ${v.metodo_pago}`;
            info.append(titulo, sub);

            const enlacePdf = document.createElement("a");
            enlacePdf.href = `${API_BASE_URL}/api/tienda/boleta/${v.id}/pdf`;
            enlacePdf.target = "_blank";
            enlacePdf.rel = "noopener noreferrer";
            enlacePdf.className = "btn btn-outline-primary btn-sm";
            enlacePdf.textContent = "Ver PDF";

            card.append(info, enlacePdf);
            tablaVentas.append(card);
        }
    }

    function renderizarInventario(productos) {
        listaInventario.replaceChildren();
        for (const p of productos) {
            const item = document.createElement("div");
            item.className = "p-2 border rounded bg-white d-flex justify-content-between align-items-center";
            const nombre = document.createElement("span");
            nombre.className = "small";
            nombre.textContent = `${p.codigo} · ${p.nombre}`;
            const stock = document.createElement("strong");
            stock.className = "small ms-2";
            stock.textContent = `${p.stock} unid.`;
            item.append(nombre, stock);
            listaInventario.append(item);
        }
    }

    async function cargarCrm() {
        try {
            const sesion = await asegurarSesionAdminParaDemo();
            estadoProxyAdmin.textContent = `Sesión verificada por AuthSessionProxy: ${sesion.usuario.nombre} (Rol: ${sesion.usuario.rol.toUpperCase()}).`;
            const data = await peticionApi("/api/admin/crm");
            const r = data.resumen || {};
            kpiIngresos.textContent = `S/ ${Number(r.ingresos_totales || 0).toFixed(2)}`;
            kpiVentas.textContent = String(r.total_ventas || 0);
            kpiUsuarios.textContent = `${r.usuarios_activos || 0} / ${r.total_usuarios || 0}`;
            kpiStock.textContent = String(r.stock_total_unidades || 0);

            renderizarUsuarios(data.usuarios || []);
            renderizarVentas(data.ventas || []);
            renderizarInventario(data.productos || []);
        } catch (error) {
            estadoProxyAdmin.textContent = `Aviso Proxy/FastAPI: ${error.message}`;
        }
    }

    btnRefrescar.addEventListener("click", cargarCrm);
    cargarCrm();
})();
