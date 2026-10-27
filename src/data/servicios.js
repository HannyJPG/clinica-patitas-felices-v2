export const servicios = Object.freeze([
    { id: "consulta-general", titulo: "Consulta general", descripcion: "Cuéntanos qué necesita tu mascota y solicita una cita para conocer su estado de bienestar.", icono: "M6 3v5a4 4 0 0 0 8 0V3M4 3h4m4 0h4m-6 9v3a5 5 0 0 0 10 0v-2m0-4a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z" },
    { id: "vacunacion", titulo: "Vacunación", descripcion: "Elige este servicio para conversar sobre la vacunación y la atención que necesita tu mascota.", icono: "m15 3 6 6M18 6l-3 3m-8 2 6 6m-8 2 2 2 10-10-6-6L1 15l4 4Zm0 0-3 3" },
    { id: "desparasitacion", titulo: "Desparasitación", descripcion: "Solicita orientación y una visita para el cuidado preventivo de tu compañero.", icono: "M12 3 3 7v5c0 5 9 9 9 9s9-4 9-9V7l-9-4Zm-4 9 3 3 5-6" },
    { id: "control", titulo: "Control y seguimiento", descripcion: "Da continuidad a su atención y comparte cómo se encuentra en su próxima visita.", icono: "M20 8a5 5 0 0 0-8-4 5 5 0 0 0-8 4c0 5 8 12 8 12s8-7 8-12ZM4 12h5l2-3 2 6 2-3h5" }
]);
export const SERVICIOS = Object.freeze(Object.fromEntries(servicios.map(servicio => [servicio.id, servicio.titulo])));
