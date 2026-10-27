import { test } from "node:test";
import assert from "node:assert/strict";
import { validarCita, obtenerMomentoLima, servicioDesdeBusqueda } from "../src/scripts/validar-cita.js";

const ahora = new Date("2026-10-26T15:30:45Z"); // 10:30 en Lima.
const cita = {
    propietario: "María Pérez",
    telefono: "+51 987 654 321",
    mascota: "Luna",
    servicio: "consulta-general",
    fecha: "2026-10-27",
    hora: "09:00",
    motivo: "Consulta de control de mi mascota."
};

test("acepta una solicitud futura completa y elimina espacios exteriores", () => {
    const { errores, valores } = validarCita({ ...cita, propietario: "  María Pérez  " }, ahora);
    assert.deepEqual(errores, {});
    assert.equal(valores.propietario, "María Pérez");
});

test("rechaza todos los campos vacíos o compuestos solo de espacios", () => {
    const campos = Object.keys(cita);
    for (const valor of ["", "   "]) {
        const datos = Object.fromEntries(campos.map(campo => [campo, valor]));
        assert.deepEqual(Object.keys(validarCita(datos, ahora).errores).sort(), [...campos].sort());
    }
});

test("rechaza nombres y motivos que exceden sus límites", () => {
    for (const [campo, valor] of [["propietario", "a"], ["propietario", "a".repeat(81)], ["mascota", "a".repeat(61)], ["motivo", "corto"], ["motivo", "a".repeat(1001)]]) {
        assert.ok(validarCita({ ...cita, [campo]: valor }, ahora).errores[campo], campo);
    }
});

test("acepta nombres con acentos, apóstrofos y mascotas con un solo carácter", () => {
    assert.deepEqual(validarCita({ ...cita, propietario: "Ana O'Connor", mascota: "Q" }, ahora).errores, {});
});

test("acepta teléfonos locales e internacionales con separadores", () => {
    for (const telefono of ["987654321", "+51 987 654 321", "+1 (212) 555-1234", "123456789012345"]) {
        assert.equal(validarCita({ ...cita, telefono }, ahora).errores.telefono, undefined, telefono);
    }
});

test("rechaza teléfonos con letras, pocos dígitos, demasiados dígitos o signos incorrectos", () => {
    for (const telefono of ["98765", "987abc321", "         ", "---------", "1234567890123456", "987+654321", "++51987654321", "987654321<script>"]) {
        assert.ok(validarCita({ ...cita, telefono }, ahora).errores.telefono, telefono);
    }
});

test("acepta cada servicio del formulario y rechaza valores manipulados", () => {
    for (const servicio of ["consulta-general", "vacunacion", "desparasitacion", "control"]) {
        assert.deepEqual(validarCita({ ...cita, servicio }, ahora).errores, {});
    }
    for (const servicio of ["otro", "toString", "__proto__"]) {
        assert.ok(validarCita({ ...cita, servicio }, ahora).errores.servicio);
    }
});

test("rechaza fechas pasadas, imposibles o con un formato incorrecto", () => {
    for (const fecha of ["2026-10-25", "2026-02-30", "2026-13-01", "2026-11-31", "27/10/2026", "2027-02-29"]) {
        assert.ok(validarCita({ ...cita, fecha }, ahora).errores.fecha, fecha);
    }
});

test("acepta el 29 de febrero de un año bisiesto futuro", () => {
    assert.deepEqual(validarCita({ ...cita, fecha: "2028-02-29" }, ahora).errores, {});
});

test("rechaza horas incorrectas y horas ya transcurridas de hoy", () => {
    for (const hora of ["24:00", "09:60", "9:00", "09:00:30", "abc", "10:29", "10:30"]) {
        assert.ok(validarCita({ ...cita, fecha: "2026-10-26", hora }, ahora).errores.hora, hora);
    }
});

test("acepta una hora posterior hoy y cualquier hora válida en una fecha futura", () => {
    assert.deepEqual(validarCita({ ...cita, fecha: "2026-10-26", hora: "11:00" }, ahora).errores, {});
    for (const hora of ["00:00", "23:30"]) {
        assert.deepEqual(validarCita({ ...cita, hora }, ahora).errores, {});
    }
});

test("usa la fecha de Lima aunque UTC ya esté en el día siguiente", () => {
    const cercaDeMedianoche = new Date("2026-10-27T04:58:00Z");
    assert.deepEqual(obtenerMomentoLima(cercaDeMedianoche), { fecha: "2026-10-26", hora: "23:58" });
    assert.ok(validarCita({ ...cita, fecha: "2026-10-26", hora: "23:30" }, cercaDeMedianoche).errores.hora);
    assert.deepEqual(validarCita({ ...cita, fecha: "2026-10-27", hora: "00:00" }, cercaDeMedianoche).errores, {});
    const antesDelUltimoTurno = new Date("2026-10-27T04:28:00Z");
    assert.deepEqual(validarCita({ ...cita, fecha: "2026-10-26", hora: "23:30" }, antesDelUltimoTurno).errores, {});
});

test("actualiza la comparación al pasar medianoche en Lima", () => {
    const medianoche = new Date("2026-10-27T05:00:00Z");
    assert.deepEqual(obtenerMomentoLima(medianoche), { fecha: "2026-10-27", hora: "00:00" });
    assert.ok(validarCita({ ...cita, fecha: "2026-10-26", hora: "23:59" }, medianoche).errores.fecha);
});

test("no altera los datos originales", () => {
    const original = Object.freeze({ ...cita, mascota: "  Luna  " });
    const { valores } = validarCita(original, ahora);
    assert.equal(original.mascota, "  Luna  ");
    assert.equal(valores.mascota, "Luna");
});

test("los enlaces de servicios preseleccionan solo opciones conocidas", () => {
    assert.equal(servicioDesdeBusqueda("?servicio=vacunacion"), "vacunacion");
    assert.equal(servicioDesdeBusqueda("?servicio=consulta-general&otro=valor"), "consulta-general");
    for (const busqueda of ["", "?servicio=", "?servicio=inexistente", "?servicio=__proto__", "?servicio=%3Cscript%3E"]) {
        assert.equal(servicioDesdeBusqueda(busqueda), "");
    }
});

test("las horas deben corresponder a intervalos de media hora", () => {
    for (const hora of ["09:00", "09:30", "10:00", "18:30"]) {
        assert.equal(validarCita({ ...cita, hora }, ahora).errores.hora, undefined, hora);
    }
    for (const hora of ["09:01", "09:15", "10:31", "18:45", "23:59"]) {
        assert.match(validarCita({ ...cita, hora }, ahora).errores.hora, /30 minutos/, hora);
    }
});
