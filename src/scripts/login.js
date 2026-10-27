import { peticionApi, guardarSesion, obtenerSesion, cerrarSesion } from "./api-client.js";

(() => {
    const formulario = document.getElementById("formulario-login");
    if (!formulario) return;

    const inputEmail = document.getElementById("login-email");
    const inputPass = document.getElementById("login-password");
    const alerta = document.getElementById("alerta-login");
    const btnCerrar = document.getElementById("btn-cerrar-sesion");
    const panelSesion = document.getElementById("panel-sesion-activa");
    const etiquetaRol = document.getElementById("sesion-rol-etiqueta");
    const bienvenida = document.getElementById("sesion-bienvenida");
    const listaPermisos = document.getElementById("sesion-lista-permisos");
    const enlaceVista = document.getElementById("enlace-ir-vista");

    function renderizarSesion(datos) {
        if (!datos?.usuario || !datos?.rbac) {
            panelSesion.hidden = true;
            btnCerrar.hidden = true;
            return;
        }
        etiquetaRol.textContent = `Rol activo: ${datos.rbac.etiqueta}`;
        bienvenida.textContent = `${datos.usuario.nombre} (${datos.usuario.email}) — Estado en BD: ${datos.usuario.estado.toUpperCase()}`;
        listaPermisos.replaceChildren();
        for (const permiso of datos.rbac.acciones || []) {
            const li = document.createElement("li");
            li.textContent = permiso;
            listaPermisos.append(li);
        }
        enlaceVista.href = datos.rbac.ruta_principal || "/tienda";
        enlaceVista.textContent = `Abrir vista asignada (${datos.rbac.ruta_principal})`;
        panelSesion.hidden = false;
        btnCerrar.hidden = false;
    }

    document.querySelectorAll("[data-demo-email]").forEach(boton => {
        boton.addEventListener("click", () => {
            inputEmail.value = boton.getAttribute("data-demo-email") || "";
            inputPass.value = boton.getAttribute("data-demo-pass") || "";
            alerta.hidden = true;
        });
    });

    formulario.addEventListener("submit", async evento => {
        evento.preventDefault();
        alerta.hidden = true;
        try {
            const respuesta = await peticionApi("/api/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    email: inputEmail.value.trim(),
                    password: inputPass.value
                })
            });
            guardarSesion(respuesta);
            renderizarSesion(respuesta);
        } catch (error) {
            panelSesion.hidden = true;
            alerta.textContent = error.message || "No se pudo iniciar sesión.";
            alerta.hidden = false;
        }
    });

    btnCerrar.addEventListener("click", () => {
        cerrarSesion();
        panelSesion.hidden = true;
        btnCerrar.hidden = true;
        alerta.hidden = true;
    });

    const sesionGuardada = obtenerSesion();
    if (sesionGuardada) {
        renderizarSesion(sesionGuardada);
    }
})();
