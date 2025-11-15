@echo off
REM ============================================================================
REM INICIAR DASHBOARD MERCADO AUTOMOTOR
REM ============================================================================
REM Este script inicia automáticamente:
REM 0. Verificación de entorno virtual
REM 1. Actualización de datos externos (BCRA e INDEC)
REM 2. Revisión de datos nuevos para agregar
REM 3. Terminal con Streamlit
REM 4. Terminal con ngrok
REM ============================================================================

REM Guardar el directorio actual
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo.
echo ========================================================================
echo   INICIANDO DASHBOARD MERCADO AUTOMOTOR
echo ========================================================================
echo.
echo Directorio del proyecto: %PROJECT_DIR%
echo.

REM [0/5] Verificar si existe entorno virtual
echo [0/5] Verificando entorno virtual...
if exist "venv\Scripts\activate.bat" (
    echo [OK] Entorno virtual encontrado
    set PYTHON_CMD=venv\Scripts\python.exe
    set STREAMLIT_CMD=venv\Scripts\streamlit.exe
) else (
    echo [INFO] No se encontro entorno virtual, usando Python del sistema
    set PYTHON_CMD=python
    set STREAMLIT_CMD=streamlit
)
echo.

REM [1/5] Actualizar datos externos
echo [1/5] Actualizando datos externos (BCRA e INDEC)...
echo.

%PYTHON_CMD% backend\data_processing\actualizar_datos_externos.py

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

timeout /t 2 /nobreak >nul

REM [2/5] Revisar datos nuevos para agregar
echo [2/5] Revisando datos nuevos de inscripciones/transferencias/prendas...
echo.

REM Verificar si hay archivos CSV nuevos en INPUT
set HAY_DATOS_NUEVOS=0
if exist "INPUT\INSCRIPCIONES\*.csv" set HAY_DATOS_NUEVOS=1
if exist "INPUT\TRANSFERENCIAS\*.csv" set HAY_DATOS_NUEVOS=1
if exist "INPUT\PRENDAS\*.csv" set HAY_DATOS_NUEVOS=1

if %HAY_DATOS_NUEVOS%==1 (
    echo [ENCONTRADO] Hay archivos CSV nuevos para procesar:
    echo.
    dir /b INPUT\INSCRIPCIONES\*.csv 2>nul
    dir /b INPUT\TRANSFERENCIAS\*.csv 2>nul
    dir /b INPUT\PRENDAS\*.csv 2>nul
    echo.
    echo ¿Desea procesarlos AHORA? (esto puede tardar varios minutos^)
    choice /C SN /M "Presione S para procesar ahora, N para saltear"
    if ERRORLEVEL 2 (
        echo [OMITIDO] Procesamiento de datos nuevos omitido
    ) else (
        echo [PROCESANDO] Cargando datos nuevos a PostgreSQL...
        %PYTHON_CMD% scripts\cargar_datos_gob_ar_postgresql.py
        if %ERRORLEVEL% EQU 0 (
            echo [OK] Datos nuevos cargados exitosamente
        ) else (
            echo [ERROR] Hubo problemas al cargar los datos
        )
    )
) else (
    echo [OK] No hay archivos CSV nuevos pendientes
)
echo.

timeout /t 2 /nobreak >nul

echo [3/5] Abriendo terminal para Streamlit...

REM Terminal 1: Streamlit
start "STREAMLIT - Dashboard Mercado Automotor" powershell -NoExit -Command "cd '%PROJECT_DIR%'; Write-Host ''; Write-Host '====================================================================' -ForegroundColor Cyan; Write-Host '  STREAMLIT - DASHBOARD MERCADO AUTOMOTOR' -ForegroundColor Cyan; Write-Host '====================================================================' -ForegroundColor Cyan; Write-Host ''; Write-Host 'Directorio: %PROJECT_DIR%' -ForegroundColor Gray; Write-Host ''; Write-Host '[+] Activando entorno virtual...' -ForegroundColor Green; if (Test-Path 'venv\Scripts\Activate.ps1') { .\venv\Scripts\Activate.ps1; Write-Host '[OK] Entorno virtual activado' -ForegroundColor Green } else { Write-Host '[INFO] Usando Python del sistema' -ForegroundColor Yellow }; Write-Host ''; Write-Host '[+] Iniciando Streamlit...' -ForegroundColor Green; Write-Host ''; streamlit run frontend/app_datos_gob.py"

REM Esperar 5 segundos para que Streamlit inicie
timeout /t 5 /nobreak >nul

echo [4/5] Abriendo terminal para ngrok...

REM Terminal 2: ngrok
start "NGROK - Tunel Publico" powershell -NoExit -Command "Write-Host ''; Write-Host '====================================================================' -ForegroundColor Yellow; Write-Host '  NGROK - TUNEL PUBLICO' -ForegroundColor Yellow; Write-Host '====================================================================' -ForegroundColor Yellow; Write-Host ''; Write-Host '[+] Iniciando ngrok...' -ForegroundColor Green; Write-Host ''; Write-Host 'IMPORTANTE: Copia la URL que aparece en FORWARDING' -ForegroundColor Cyan; Write-Host 'Ejemplo: https://xxxx-xx-xx.ngrok-free.app' -ForegroundColor Cyan; Write-Host ''; Write-Host 'Nota: Si ngrok no funciona, instalalo con: choco install ngrok' -ForegroundColor Gray; Write-Host '      o descargalo desde: https://ngrok.com/download' -ForegroundColor Gray; Write-Host ''; ngrok http 8501"

echo [5/5] Terminales abiertas exitosamente!
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
