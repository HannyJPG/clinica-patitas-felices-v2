import { SERVICIOS } from "../data/servicios.js";
import { clinica } from "../data/clinica.js";

const CAMPOS = Object.freeze(["propietario", "telefono", "mascota", "servicio", "fecha", "hora", "motivo"]);

function servicioDesdeBusqueda(busqueda = "") {
    const servicio = new URLSearchParams(busqueda).get("servicio");
    return Object.hasOwn(SERVICIOS, servicio) ? servicio : "";
}

function obtenerMomentoLima(ahora = new Date()) {
    const partes = new Intl.DateTimeFormat("en-CA", {
        timeZone: clinica.zonaHoraria,
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
    } else if ((Number(valores.hora.slice(0, 2)) * 60 + Number(valores.hora.slice(3))) % clinica.duracionCitaMinutos !== 0) {
        errores.hora = "Elige una hora en intervalos de 30 minutos, por ejemplo 09:00 o 09:30.";
    } else if (!errores.fecha && valores.fecha === momento.fecha && valores.hora <= momento.hora) {
        errores.hora = "Para hoy, elige una hora posterior a la actual en Lima, Perú.";
    }

    if (valores.motivo.length < 10 || valores.motivo.length > 1000) {
        errores.motivo = "Describe el motivo en 10 a 1000 caracteres, sin contar espacios al inicio o al final.";
    }

    return { valores, errores };
}


export { CAMPOS, SERVICIOS, obtenerMomentoLima, validarCita, servicioDesdeBusqueda };
