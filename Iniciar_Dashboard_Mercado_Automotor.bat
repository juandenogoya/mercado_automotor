@echo off
REM ============================================================================
REM INICIAR DASHBOARD MERCADO AUTOMOTOR
REM ============================================================================
REM Este script inicia automáticamente:
REM 0. Actualización de datos externos (BCRA e INDEC)
REM 1. Terminal con Streamlit
REM 2. Terminal con ngrok
REM ============================================================================

echo.
echo ========================================================================
echo   INICIANDO DASHBOARD MERCADO AUTOMOTOR
echo ========================================================================
echo.
echo [1/4] Actualizando datos externos (BCRA e INDEC)...
echo.

REM Ejecutar actualización de datos
python backend/data_processing/actualizar_datos_externos.py

REM Verificar si la actualización fue exitosa
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Datos actualizados correctamente
    echo.
) else (
    echo.
    echo [ADVERTENCIA] Algunos datos no pudieron actualizarse
    echo [INFO] El dashboard iniciara con los datos existentes
    echo.
)

REM Esperar 3 segundos antes de continuar
timeout /t 3 /nobreak >nul

echo [2/4] Abriendo terminal para Streamlit...

REM Terminal 1: Streamlit
start "STREAMLIT - Dashboard Mercado Automotor" powershell -NoExit -Command "cd C:\Users\juand\OneDrive\Escritorio\concecionaria\mercado_automotor; Write-Host ''; Write-Host '====================================================================' -ForegroundColor Cyan; Write-Host '  STREAMLIT - DASHBOARD MERCADO AUTOMOTOR' -ForegroundColor Cyan; Write-Host '====================================================================' -ForegroundColor Cyan; Write-Host ''; Write-Host '[+] Iniciando Streamlit...' -ForegroundColor Green; Write-Host ''; streamlit run frontend/app_datos_gob.py"

REM Esperar 5 segundos para que Streamlit inicie
timeout /t 5 /nobreak >nul

echo [3/4] Abriendo terminal para ngrok...

REM Terminal 2: ngrok
start "NGROK - Tunel Publico" powershell -NoExit -Command "Write-Host ''; Write-Host '====================================================================' -ForegroundColor Yellow; Write-Host '  NGROK - TUNEL PUBLICO' -ForegroundColor Yellow; Write-Host '====================================================================' -ForegroundColor Yellow; Write-Host ''; Write-Host '[+] Iniciando ngrok...' -ForegroundColor Green; Write-Host ''; Write-Host 'IMPORTANTE: Copia la URL que aparece en FORWARDING' -ForegroundColor Cyan; Write-Host 'Ejemplo: https://xxxx-xx-xx.ngrok-free.app' -ForegroundColor Cyan; Write-Host ''; ngrok http 8501"

echo [4/4] Terminales abiertas exitosamente!
echo.
echo ========================================================================
echo   INSTRUCCIONES
echo ========================================================================
echo.
echo 1. Terminal STREAMLIT: Espera a ver "You can now view your Streamlit app"
echo 2. Terminal NGROK: Copia la URL en "Forwarding" (https://xxxx.ngrok-free.app)
echo 3. Abre tu navegador:
echo    - Local: http://localhost:8501
echo    - Publico: La URL de ngrok
echo.
echo Para DETENER:
echo    - Presiona Ctrl+C en cada terminal
echo    - O cierra las ventanas
echo.
echo ========================================================================

REM Esperar 3 segundos antes de cerrar esta ventana
timeout /t 3 /nobreak >nul

REM Cerrar esta ventana de comando
exit
