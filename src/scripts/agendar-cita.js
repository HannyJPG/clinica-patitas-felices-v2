import { CAMPOS, SERVICIOS, obtenerMomentoLima, validarCita, servicioDesdeBusqueda } from "./validar-cita.js";
import { enlaceWhatsApp, mensajeSolicitudCita } from "./whatsapp.js";
import { peticionApi } from "./api-client.js";

(() => {
    const formulario = document.getElementById("formulario-cita");
    if (!formulario) return;

    const controles = Object.fromEntries(CAMPOS.map(campo => [campo, document.getElementById(campo)]));
    const resumenErrores = document.getElementById("errores-cita");
    const listaErrores = document.getElementById("lista-errores-cita");
    const resultado = document.getElementById("resultado-cita");
    const continuarWhatsApp = document.getElementById("continuar-whatsapp");
    const botonGuardarApi = document.getElementById("guardar-cita-api");
    const estadoApiCita = document.getElementById("estado-api-cita");
    let intentoDeEnvio = false;
    let ultimosValoresValidos = null;

    const servicioInicial = servicioDesdeBusqueda(window.location.search);
    if (servicioInicial) controles.servicio.value = servicioInicial;

    function leerDatos() {
        return Object.fromEntries(CAMPOS.map(campo => [campo, controles[campo].value]));
    }

    function actualizarFechaMinima() {
        controles.fecha.min = obtenerMomentoLima().fecha;
    }

    function marcarCampo(campo, mensaje = "") {
        const control = controles[campo];
        control.setCustomValidity(mensaje);
        control.classList.toggle("is-invalid", Boolean(mensaje));
        document.getElementById(`error-${campo}`).textContent = mensaje;
        if (mensaje) control.setAttribute("aria-invalid", "true");
        else control.removeAttribute("aria-invalid");
    }

    function mostrarErrores(errores) {
        listaErrores.replaceChildren();
        for (const [campo, mensaje] of Object.entries(errores)) {
            const elemento = document.createElement("li");
            const enlace = document.createElement("a");
            enlace.href = `#${campo}`;
            enlace.textContent = mensaje;
            enlace.addEventListener("click", evento => {
                evento.preventDefault();
                controles[campo].focus();
            });
            elemento.append(enlace);
            listaErrores.append(elemento);
        }
        resumenErrores.hidden = Object.keys(errores).length === 0;
    }

    function ocultarResultado() {
        resultado.hidden = true;
        ultimosValoresValidos = null;
        continuarWhatsApp.removeAttribute("href");
        if (estadoApiCita) {
            estadoApiCita.hidden = true;
            estadoApiCita.textContent = "";
        }
        resultado.querySelectorAll("[data-resumen]").forEach(elemento => {
            elemento.textContent = "";
        });
    }

    formulario.addEventListener("submit", evento => {
        /* Preparar el resumen local. WhatsApp solo se abre al pulsar su enlace. */
        evento.preventDefault();
        intentoDeEnvio = true;
        ocultarResultado();
        actualizarFechaMinima();
        const { valores, errores } = validarCita(leerDatos());
        CAMPOS.forEach(campo => marcarCampo(campo, errores[campo]));

        /* También respetar las restricciones HTML si el navegador detecta otra infracción. */
        if (!formulario.checkValidity()) {
            CAMPOS.forEach(campo => {
                if (!controles[campo].validity.valid && !errores[campo]) {
                    errores[campo] = controles[campo].validationMessage;
                    marcarCampo(campo, errores[campo]);
                }
            });
        }

        mostrarErrores(errores);
        const primerError = CAMPOS.find(campo => errores[campo]);
        if (primerError) {
            controles[primerError].focus();
            return;
        }

        ultimosValoresValidos = valores;
        const [anio, mes, dia] = valores.fecha.split("-");
        const resumen = {
            ...valores,
            servicio: SERVICIOS[valores.servicio],
            fechaHora: `${dia}/${mes}/${anio} a las ${valores.hora} (Lima, Perú)`
        };
        resultado.querySelectorAll("[data-resumen]").forEach(elemento => {
            /* textContent muestra los datos como texto, incluso si contienen etiquetas HTML. */
            elemento.textContent = resumen[elemento.dataset.resumen];
        });
        continuarWhatsApp.href = enlaceWhatsApp(mensajeSolicitudCita(valores));
        resultado.hidden = false;
        resultado.focus();
    });

    botonGuardarApi?.addEventListener("click", async () => {
        if (!ultimosValoresValidos || !estadoApiCita) return;
        botonGuardarApi.disabled = true;
        estadoApiCita.hidden = false;
        estadoApiCita.textContent = "Conectando con FastAPI (POST /api/citas)...";
        try {
            const respuesta = await peticionApi("/api/citas", {
                method: "POST",
                body: JSON.stringify({
                    propietario: ultimosValoresValidos.propietario,
                    telefono: ultimosValoresValidos.telefono,
                    mascota_nombre: ultimosValoresValidos.mascota,
                    servicio: ultimosValoresValidos.servicio,
                    fecha: ultimosValoresValidos.fecha,
                    hora: ultimosValoresValidos.hora,
                    motivo: ultimosValoresValidos.motivo
                })
            });
            if (respuesta.whatsapp_url) {
                continuarWhatsApp.href = respuesta.whatsapp_url;
            }
            estadoApiCita.textContent = `Cita #${respuesta.cita.id} guardada en Base de Datos y adaptada con WhatsAppAdapter.`;
        } catch (error) {
            estadoApiCita.textContent = `Aviso: ${error.message}. El enlace de WhatsApp sigue listo para enviarse.`;
        } finally {
            botonGuardarApi.disabled = false;
        }
    });

    function revisarCambio(evento) {
        ocultarResultado();
        resumenErrores.hidden = true;
        const campo = evento.target.name;
        if (!intentoDeEnvio || !CAMPOS.includes(campo)) return;
        const { errores } = validarCita(leerDatos());
        marcarCampo(campo, errores[campo]);
        if (campo === "fecha") marcarCampo("hora", errores.hora);
    }
    formulario.addEventListener("input", revisarCambio);
    formulario.addEventListener("change", revisarCambio);

    formulario.addEventListener("reset", () => {
        intentoDeEnvio = false;
        ocultarResultado();
        resumenErrores.hidden = true;
        listaErrores.replaceChildren();
        CAMPOS.forEach(campo => marcarCampo(campo));
        actualizarFechaMinima();
    });

    controles.fecha.addEventListener("focus", actualizarFechaMinima);
    actualizarFechaMinima();
    /* Si el script no llega hasta aquí, los campos siguen deshabilitados. */
    document.getElementById("campos-cita").disabled = false;
})();
