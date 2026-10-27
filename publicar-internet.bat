@echo off
title Clinica Veterinaria Patitas Felices - Hosting Publico en Internet
cd /d "%~dp0"
call npm.cmd run build
node scripts/publicar-internet.mjs
pause
