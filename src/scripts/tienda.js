import { peticionApi, obtenerSesion, guardarSesion, descargarPdfDesdeBase64 } from "./api-client.js";

(() => {
    const gridProductos = document.getElementById("grid-productos");
    if (!gridProductos) return;

    const listaPedido = document.getElementById("lista-pedido");
    const elSubtotal = document.getElementById("resumen-subtotal");
    const elIgv = document.getElementById("resumen-igv");
    const elTotal = document.getElementById("resumen-total");
    const formCheckout = document.getElementById("formulario-checkout");
    const alertaCheckout = document.getElementById("alerta-checkout");
    const btnVaciar = document.getElementById("btn-vaciar-pedido");
    const seccionBoleta = document.getElementById("resultado-boleta");
    const elNumeroBoleta = document.getElementById("boleta-numero");
    const btnDescargarPdf = document.getElementById("btn-descargar-pdf");
    const enlaceWhatsappBoleta = document.getElementById("enlace-whatsapp-boleta");
    const estadoCatalogo = document.getElementById("estado-catalogo");

    const carrito = new Map();
    let ultimoPdfBase64 = null;
    let ultimoNombrePdf = "Boleta_Patitas_Felices.pdf";

    function calcularTotales() {
        let total = 0;
        for (const item of carrito.values()) {
            total += item.precio * item.cantidad;
        }
        const totalRedondeado = Math.round(total * 100) / 100;
        const subtotal = Math.round((totalRedondeado / 1.18) * 100) / 100;
        const igv = Math.round((totalRedondeado - subtotal) * 100) / 100;
        elSubtotal.textContent = `S/ ${subtotal.toFixed(2)}`;
        elIgv.textContent = `S/ ${igv.toFixed(2)}`;
        elTotal.textContent = `S/ ${totalRedondeado.toFixed(2)}`;
    }

    function renderizarCarrito() {
        listaPedido.replaceChildren();
        if (carrito.size === 0) {
            const p = document.createElement("p");
            p.className = "small-note mb-0";
            p.textContent = "Aún no has seleccionado productos del catálogo.";
            listaPedido.append(p);
            calcularTotales();
            return;
        }

        const ul = document.createElement("ul");
        ul.className = "list-unstyled mb-0 d-grid gap-2";
        for (const [id, item] of carrito.entries()) {
            const li = document.createElement("li");
            li.className = "d-flex justify-content-between align-items-center p-2 border rounded";
            const info = document.createElement("span");
            info.className = "small";
            info.textContent = `${item.cantidad}x ${item.nombre}`;
            const importe = document.createElement("strong");
            importe.className = "small ms-2";
            importe.textContent = `S/ ${(item.precio * item.cantidad).toFixed(2)}`;
            li.append(info, importe);
            ul.append(li);
        }
        listaPedido.append(ul);
        calcularTotales();
    }

    function vincularBotonesProducto() {
        gridProductos.querySelectorAll("[data-seleccionar-producto]").forEach(boton => {
            boton.addEventListener("click", () => {
                const id = Number(boton.getAttribute("data-seleccionar-producto"));
                const nombre = boton.getAttribute("data-nombre") || "Producto";
                const precio = Number(boton.getAttribute("data-precio") || 0);
                const actual = carrito.get(id) || { producto_id: id, nombre, precio, cantidad: 0 };
                actual.cantidad += 1;
                carrito.set(id, actual);
                seccionBoleta.hidden = true;
                alertaCheckout.hidden = true;
                renderizarCarrito();
            });
        });
    }

    async function sincronizarCatalogoDesdeApi() {
        try {
            const data = await peticionApi("/api/productos");
            if (!Array.isArray(data?.productos)) return;
            for (const prod of data.productos) {
                const badge = document.querySelector(`[data-stock-badge="${prod.id}"]`);
                if (badge) badge.textContent = `Stock: ${prod.stock}`;
            }
            estadoCatalogo.textContent = "Conectado en vivo con FastAPI";
        } catch {
            estadoCatalogo.textContent = "Catálogo local listo";
        }
    }

    async function asegurarSesionClienteParaDemo() {
        const sesion = obtenerSesion();
        if (sesion?.token) return sesion;
        const loginDemo = await peticionApi("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({
                email: "cliente@patitasfelices.pe",
                password: "cliente123"
            })
        });
        guardarSesion(loginDemo);
        return loginDemo;
    }

    formCheckout.addEventListener("submit", async evento => {
        evento.preventDefault();
        alertaCheckout.hidden = true;
        seccionBoleta.hidden = true;

        if (carrito.size === 0) {
            alertaCheckout.textContent = "Selecciona al menos un producto del catálogo antes de procesar la compra.";
            alertaCheckout.hidden = false;
            return;
        }

        const clienteNombre = document.getElementById("cliente-nombre").value.trim();
        const clienteDocumento = document.getElementById("cliente-documento").value.trim();
        const metodoPago = document.getElementById("metodo-pago").value;

        try {
            await asegurarSesionClienteParaDemo();
            const respuesta = await peticionApi("/api/tienda/checkout", {
                method: "POST",
                body: JSON.stringify({
                    cliente_nombre: clienteNombre,
                    cliente_documento: clienteDocumento,
                    metodo_pago: metodoPago,
                    items: Array.from(carrito.values()).map(i => ({
                        producto_id: i.producto_id,
                        cantidad: i.cantidad
                    }))
                })
            });

            ultimoPdfBase64 = respuesta.pdf_base64;
            ultimoNombrePdf = respuesta.pdf_filename || `Boleta_${respuesta.venta.numero_boleta}.pdf`;
            elNumeroBoleta.textContent = respuesta.venta.numero_boleta;
            if (respuesta.whatsapp_url) {
                enlaceWhatsappBoleta.href = respuesta.whatsapp_url;
            }
            seccionBoleta.hidden = false;
            carrito.clear();
            renderizarCarrito();
            await sincronizarCatalogoDesdeApi();
        } catch (error) {
            alertaCheckout.textContent = error.message || "No se pudo procesar la venta en FastAPI.";
            alertaCheckout.hidden = false;
        }
    });

    btnDescargarPdf.addEventListener("click", () => {
        if (ultimoPdfBase64) {
            descargarPdfDesdeBase64(ultimoPdfBase64, ultimoNombrePdf);
        }
    });

    btnVaciar.addEventListener("click", () => {
        carrito.clear();
        alertaCheckout.hidden = true;
        seccionBoleta.hidden = true;
        renderizarCarrito();
    });

    vincularBotonesProducto();
    sincronizarCatalogoDesdeApi();
})();
