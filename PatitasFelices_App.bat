@echo off
title Clinica Veterinaria Patitas Felices - Modo App Nativa
cd /d "%~dp0"
echo =========================================================================
echo   CLINICA VETERINARIA PATITAS FELICES - EJECUTABLE MODO APP
echo   16 Tablas (prueba_1.erd.json) + 4 Patrones GoF + Boleta PDF
echo =========================================================================

if not exist "dist\index.html" (
    echo Compilando interfaz Astro...
    call npm.cmd run build
)

echo Iniciando motor unificado FastAPI + Base de Datos (16 Tablas)...
start "Servidor Patitas Felices" /min cmd /c "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo Abriendo Aplicacion de Escritorio Patitas Felices...
start msedge --app=http://127.0.0.1:8000
exit
