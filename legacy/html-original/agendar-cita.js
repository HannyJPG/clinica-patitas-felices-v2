/* Demostración local: no hace peticiones ni persiste los datos del formulario. */
(() => {
    "use strict";

    const CAMPOS = Object.freeze(["propietario", "telefono", "mascota", "servicio", "fecha", "hora", "motivo"]);
    const SERVICIOS = Object.freeze({
        "consulta-general": "Consulta general",
        vacunacion: "Vacunación",
        desparasitacion: "Desparasitación",
        control: "Control y seguimiento"
    });

    function obtenerMomentoLima(ahora = new Date()) {
        const partes = new Intl.DateTimeFormat("en-CA", {
            timeZone: "America/Lima",
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            hourCycle: "h23"
        }).formatToParts(ahora);
        const valores = Object.fromEntries(partes.map(parte => [parte.type, parte.value]));
        return {
            fecha: `${valores.year}-${valores.month}-${valores.day}`,
            hora: `${valores.hour}:${valores.minute}`
        };
    }

    function esFechaValida(fecha) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) return false;
        const fechaUTC = new Date(`${fecha}T00:00:00.000Z`);
        return !Number.isNaN(fechaUTC.getTime()) && fechaUTC.toISOString().slice(0, 10) === fecha;
    }

    function validarCita(datos, ahora = new Date()) {
        const valores = Object.fromEntries(CAMPOS.map(campo => [campo, String(datos?.[campo] ?? "").trim()]));
        const errores = {};
        const momento = obtenerMomentoLima(ahora);

        if (valores.propietario.length < 2 || valores.propietario.length > 80) {
            errores.propietario = "Escribe el nombre del propietario en 2 a 80 caracteres, sin contar espacios al inicio o al final.";
        }

        const digitos = valores.telefono.replace(/\D/g, "");
        if (!/^\+?[0-9 ()-]+$/.test(valores.telefono) || digitos.length < 9 || digitos.length > 15 || valores.telefono.length > 25) {
            errores.telefono = "Escribe un teléfono de 9 a 15 dígitos. Puedes incluir + al inicio, espacios, guiones o paréntesis.";
        }

        if (!valores.mascota || valores.mascota.length > 60) {
            errores.mascota = "Escribe el nombre de tu mascota, de hasta 60 caracteres.";
        }

        if (!Object.hasOwn(SERVICIOS, valores.servicio)) {
            errores.servicio = "Selecciona uno de los servicios de la lista.";
        }

        if (!esFechaValida(valores.fecha)) {
            errores.fecha = "Selecciona una fecha válida.";
        } else if (valores.fecha < momento.fecha) {
            errores.fecha = "La fecha no puede ser anterior a hoy en Lima, Perú.";
        }

        if (!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(valores.hora)) {
            errores.hora = "Selecciona una hora válida, con horas y minutos.";
        } else if (!errores.fecha && valores.fecha === momento.fecha && valores.hora <= momento.hora) {
            errores.hora = "Para hoy, elige una hora posterior a la actual en Lima, Perú.";
        }

        if (valores.motivo.length < 10 || valores.motivo.length > 1000) {
            errores.motivo = "Describe el motivo en 10 a 1000 caracteres, sin contar espacios al inicio o al final.";
        }

        return { valores, errores };
    }

    /* Permite probar las mismas reglas con node --test, sin navegador ni datos reales. */
    if (typeof module !== "undefined" && module.exports) {
        module.exports = { validarCita, obtenerMomentoLima };
    }
    if (typeof document === "undefined") return;

    const formulario = document.getElementById("formulario-cita");
    if (!formulario) return;

    const controles = Object.fromEntries(CAMPOS.map(campo => [campo, document.getElementById(campo)]));
    const resumenErrores = document.getElementById("errores-cita");
    const listaErrores = document.getElementById("lista-errores-cita");
    const resultado = document.getElementById("resultado-cita");
    let intentoDeEnvio = false;

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
        resultado.querySelectorAll("[data-resumen]").forEach(elemento => {
            elemento.textContent = "";
        });
    }

    formulario.addEventListener("submit", evento => {
        /* Siempre interceptar antes de validar: nunca enviar este formulario a una URL. */
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
        resultado.hidden = false;
        resultado.focus();
    });

    formulario.addEventListener("input", evento => {
        ocultarResultado();
        resumenErrores.hidden = true;
        const campo = evento.target.name;
        if (!intentoDeEnvio || !CAMPOS.includes(campo)) return;
        const { errores } = validarCita(leerDatos());
        marcarCampo(campo, errores[campo]);
        if (campo === "fecha") marcarCampo("hora", errores.hora);
    });

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
