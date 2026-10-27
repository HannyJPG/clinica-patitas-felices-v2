import { spawn } from "node:child_process";

console.log("=========================================================================");
console.log("  CLÍNICA VETERINARIA PATITAS FELICES - INICIANDO TODO EL SISTEMA");
console.log("=========================================================================");
console.log("  1. Frontend Astro (Landing)    : http://127.0.0.1:4321/");
console.log("  2. Login y Roles RBAC          : http://127.0.0.1:4321/login");
console.log("  3. Vista Cliente (Tienda PDF)  : http://127.0.0.1:4321/tienda");
console.log("  4. Vista Doctor (Agenda)       : http://127.0.0.1:4321/doctor");
console.log("  5. Vista Admin (CRM Dashboard) : http://127.0.0.1:4321/admin");
console.log("  6. Visor de Base de Datos (6)  : http://127.0.0.1:8000/visor-bd");
console.log("  7. Swagger UI (FastAPI Docs)   : http://127.0.0.1:8000/docs");
console.log("=========================================================================\n");

const backend = spawn(
    "python",
    ["-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
    { stdio: "inherit", shell: true }
);

const frontend = spawn(
    "npm.cmd",
    ["run", "dev"],
    { stdio: "inherit", shell: true }
);

function detenerProcesos() {
    backend.kill();
    frontend.kill();
    process.exit(0);
}

process.on("SIGINT", detenerProcesos);
process.on("SIGTERM", detenerProcesos);
