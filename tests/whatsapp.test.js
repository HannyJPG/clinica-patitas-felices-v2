import { test } from "node:test";
import assert from "node:assert/strict";
import { enlaceWhatsApp, mensajeSolicitudCita } from "../src/scripts/whatsapp.js";

const valores = {
    propietario: "María Pérez",
    telefono: "987654321",
    mascota: "Luna",
    servicio: "consulta-general",
    fecha: "2026-11-10",
    hora: "09:30",
    motivo: "Quisiera una consulta de control."
};

test("el enlace dirige al número confirmado, con prefijo de Perú", () => {
    const url = new URL(enlaceWhatsApp());
    assert.equal(url.protocol, "https:");
    assert.equal(url.hostname, "wa.me");
    assert.equal(url.pathname, "/51990853697");
    assert.ok(url.searchParams.get("text"));
});

test("el mensaje incluye los siete campos y la duración de 30 minutos", () => {
    const mensaje = mensajeSolicitudCita(valores);
    for (const texto of ["María Pérez", "987654321", "Luna", "Consulta general", "10/11/2026", "09:30 (Lima, Perú)", "30 minutos", valores.motivo]) {
        assert.ok(mensaje.includes(texto), texto);
    }
    assert.ok(mensaje.includes("confirmar si este horario está disponible"));
});

test("acentos, símbolos y saltos de línea se conservan sin alterar el destinatario", () => {
    const motivo = "Control de Luna & Sol 🐾\n¿Puede ser a las 09:30? #consulta";
    const mensaje = mensajeSolicitudCita({ ...valores, motivo });
    const url = new URL(enlaceWhatsApp(mensaje));
    assert.equal(url.pathname, "/51990853697");
    assert.equal(url.searchParams.get("text"), mensaje);
    assert.equal([...url.searchParams.keys()].length, 1);
    assert.equal(url.hash, "");
});

test("un texto parecido a una URL no cambia el destino de WhatsApp", () => {
    const mensaje = mensajeSolicitudCita({ ...valores, mascota: "Luna?phone=123&text=otra cosa", motivo: "Visita https://ejemplo.invalid/#contenido" });
    const url = new URL(enlaceWhatsApp(mensaje));
    assert.equal(url.origin, "https://wa.me");
    assert.equal(url.pathname, "/51990853697");
    assert.equal(url.searchParams.get("text"), mensaje);
    assert.equal(url.searchParams.has("phone"), false);
});
