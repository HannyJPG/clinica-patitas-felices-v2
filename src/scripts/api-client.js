/* Cliente HTTP fetch() hacia el Backend Python FastAPI (Local y Hosting en la Nube) */

export const API_BASE_URL =
    typeof window !== "undefined" && window.location.port !== "4321" && window.location.origin.startsWith("http")
        ? window.location.origin
        : "http://127.0.0.1:8000";

const STORAGE_KEY_SESION = "patitas_sesion_rbac_v2";

export function guardarSesion(datosLogin) {
    try {
        localStorage.setItem(STORAGE_KEY_SESION, JSON.stringify(datosLogin));
    } catch {
        /* Entornos con almacenamiento restringido */
    }
}

export function obtenerSesion() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY_SESION);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

export function cerrarSesion() {
    try {
        localStorage.removeItem(STORAGE_KEY_SESION);
    } catch {
        /* Ignorar */
    }
}

export async function peticionApi(ruta, opciones = {}) {
    const sesion = obtenerSesion();
    const cabeceras = {
        "Content-Type": "application/json",
        ...(opciones.headers || {})
    };
    if (sesion?.token && !cabeceras.Authorization) {
        cabeceras.Authorization = `Bearer ${sesion.token}`;
    }

    const respuesta = await fetch(`${API_BASE_URL}${ruta}`, {
        ...opciones,
        headers: cabeceras
    });

    const esJson = (respuesta.headers.get("content-type") || "").includes("application/json");
    const cuerpo = esJson ? await respuesta.json() : null;

    if (!respuesta.ok) {
        const mensaje = cuerpo?.detail || `Error HTTP ${respuesta.status}`;
        const error = new Error(mensaje);
        error.status = respuesta.status;
        throw error;
    }
    return cuerpo;
}

export function descargarPdfDesdeBase64(pdfBase64, nombreArchivo = "Boleta_Patitas_Felices.pdf") {
    const caracteres = atob(pdfBase64);
    const bytes = new Uint8Array(caracteres.length);
    for (let i = 0; i < caracteres.length; i += 1) {
        bytes[i] = caracteres.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: "application/pdf" });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = nombreArchivo;
    document.body.append(enlace);
    enlace.click();
    enlace.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
}
