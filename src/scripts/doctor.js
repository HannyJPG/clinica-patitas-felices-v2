import { peticionApi, obtenerSesion, guardarSesion } from "./api-client.js";

(() => {
    const contenedorCitas = document.getElementById("contenedor-citas-doctor");
    if (!contenedorCitas) return;

    const contenedorMascotas = document.getElementById("contenedor-mascotas-doctor");
    const estadoProxy = document.getElementById("estado-proxy-doctor");
    const btnRecargar = document.getElementById("btn-recargar-agenda");
    const formDiagnostico = document.getElementById("formulario-diagnostico");
    const alertaDoctor = document.getElementById("alerta-doctor");
    const inputCitaId = document.getElementById("doctor-cita-id");
    const selectEstado = document.getElementById("doctor-cita-estado");
    const inputDiag = document.getElementById("doctor-diagnostico");
    const inputTrat = document.getElementById("doctor-tratamiento");

    async function asegurarSesionDoctorParaDemo() {
        const sesion = obtenerSesion();
        if (sesion?.token && (sesion?.usuario?.rol === "doctor" || sesion?.usuario?.rol === "admin")) {
            return sesion;
        }
        const loginDoctor = await peticionApi("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({
                email: "doctor@patitasfelices.pe",
                password: "doctor123"
            })
        });
        guardarSesion(loginDoctor);
        return loginDoctor;
    }

    function renderizarCitas(citas) {
        contenedorCitas.replaceChildren();
        if (!citas.length) {
            const p = document.createElement("p");
            p.className = "small-note mb-0";
            p.textContent = "No hay citas registradas en este momento.";
            contenedorCitas.append(p);
            return;
        }

        for (const cita of citas) {
            const card = document.createElement("article");
            card.className = "p-3 border rounded bg-white";

            const cabecera = document.createElement("div");
            cabecera.className = "d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2";
            const titulo = document.createElement("strong");
            titulo.textContent = `Cita #${cita.id} · Mascota: ${cita.mascota_nombre} (${cita.servicio})`;
            const badge = document.createElement("span");
            badge.className = "status-label mb-0";
            badge.textContent = cita.estado.toUpperCase();
            cabecera.append(titulo, badge);

            const info = document.createElement("p");
            info.className = "small mb-2";
            info.textContent = `Propietario: ${cita.propietario} (Tel: ${cita.telefono}) · Fecha: ${cita.fecha} ${cita.hora}`;

            const motivo = document.createElement("p");
            motivo.className = "small-note mb-2";
            motivo.textContent = `Motivo: ${cita.motivo}`;

            const diag = document.createElement("p");
            diag.className = "small mb-2";
            diag.textContent = `Diagnóstico: ${cita.diagnostico || "Pendiente"} | Tratamiento: ${cita.tratamiento || "Pendiente"}`;

            const acciones = document.createElement("div");
            acciones.className = "d-flex flex-wrap gap-2";
            const btnSeleccionar = document.createElement("button");
            btnSeleccionar.type = "button";
            btnSeleccionar.className = "btn btn-outline-primary btn-sm";
            btnSeleccionar.textContent = "Editar diagnóstico";
            btnSeleccionar.addEventListener("click", () => {
                inputCitaId.value = String(cita.id);
                selectEstado.value = cita.estado;
                inputDiag.value = cita.diagnostico || "";
                inputTrat.value = cita.tratamiento || "";
                inputDiag.focus();
            });
            acciones.append(btnSeleccionar);

            card.append(cabecera, info, motivo, diag, acciones);
            contenedorCitas.append(card);
        }
    }

    function renderizarMascotas(mascotas) {
        contenedorMascotas.replaceChildren();
        for (const m of mascotas) {
            const col = document.createElement("div");
            col.className = "col-12 col-md-6";
            const box = document.createElement("div");
            box.className = "p-3 border rounded h-100 bg-white";
            const h3 = document.createElement("h3");
            h3.className = "h6 mb-1";
            h3.textContent = `${m.nombre} (${m.especie} · ${m.raza})`;
            const meta = document.createElement("p");
            meta.className = "small mb-1";
            meta.textContent = `Edad: ${m.edad} años · Peso: ${m.peso_kg} kg · Propietario: ${m.propietario_nombre || ""}`;
            const notas = document.createElement("p");
            notas.className = "small-note mb-0";
            notas.textContent = m.historial_resumen || "Sin antecedentes registrados.";
            box.append(h3, meta, notas);
            col.append(box);
            contenedorMascotas.append(col);
        }
    }

    async function cargarAgenda() {
        try {
            const sesion = await asegurarSesionDoctorParaDemo();
            estadoProxy.textContent = `Sesión verificada por AuthSessionProxy: ${sesion.usuario.nombre} (Rol: ${sesion.usuario.rol.toUpperCase()}).`;
            const data = await peticionApi("/api/doctor/agenda");
            renderizarCitas(data.citas || []);
            renderizarMascotas(data.mascotas || []);
        } catch (error) {
            estadoProxy.textContent = `Aviso Proxy/FastAPI: ${error.message}`;
        }
    }

    formDiagnostico.addEventListener("submit", async evento => {
        evento.preventDefault();
        alertaDoctor.hidden = true;
        try {
            await asegurarSesionDoctorParaDemo();
            const citaId = Number(inputCitaId.value);
            await peticionApi(`/api/doctor/citas/${citaId}`, {
                method: "PATCH",
                body: JSON.stringify({
                    estado: selectEstado.value,
                    diagnostico: inputDiag.value.trim(),
                    tratamiento: inputTrat.value.trim()
                })
            });
            alertaDoctor.textContent = `Cita #${citaId} actualizada correctamente en la Base de Datos.`;
            alertaDoctor.hidden = false;
            await cargarAgenda();
        } catch (error) {
            alertaDoctor.textContent = error.message || "Error al actualizar diagnóstico.";
            alertaDoctor.hidden = false;
        }
    });

    btnRecargar.addEventListener("click", cargarAgenda);
    cargarAgenda();
})();
