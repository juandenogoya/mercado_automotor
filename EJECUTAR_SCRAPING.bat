@echo off
REM Script para ejecutar scraping DNRPA en Windows
REM Doble click en este archivo para ejecutar

echo ================================================================================
echo            SCRAPING DNRPA - PATENTAMIENTOS DE AUTOS
echo ================================================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    echo Por favor instalar Python desde: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Python detectado correctamente
echo.

REM Verificar si las dependencias están instaladas
echo Verificando dependencias...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Instalando dependencias necesarias...
    pip install requests beautifulsoup4 pandas openpyxl
    echo.
)

echo.
echo Ejecutando scraping...
echo.
echo ================================================================================
echo.

REM Ejecutar el script
python scraping_local_dnrpa.py

echo.
echo ================================================================================
echo.

if errorlevel 1 (
    echo ERROR: El script termino con errores
    echo Revisa los mensajes anteriores para mas detalles
) else (
    echo EXITO: Scraping completado
    echo Busca el archivo: patentamientos_2024.xlsx
)

echo.
pause
