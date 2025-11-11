# 🚀 Acceso Directo para Iniciar Dashboard

## ¿Qué hace este archivo .bat?

El archivo `Iniciar_Dashboard_Mercado_Automotor.bat` automatiza el inicio completo del dashboard:

✅ Abre una terminal con **Streamlit** (dashboard local)
✅ Abre otra terminal con **ngrok** (URL pública)
✅ Configura todo automáticamente
✅ Muestra instrucciones en pantalla

---

## 📋 Pasos para Configurar el Acceso Directo

### Paso 1: Copiar el archivo .bat al Escritorio

```powershell
# En PowerShell, ejecutar:
cd C:\Users\juand\OneDrive\Escritorio\concecionaria\mercado_automotor

# Copiar al escritorio
copy Iniciar_Dashboard_Mercado_Automotor.bat C:\Users\juand\Desktop\
```

### Paso 2: (Opcional) Crear un ícono personalizado

1. Clic derecho en `Iniciar_Dashboard_Mercado_Automotor.bat` en el escritorio
2. Seleccionar **"Crear acceso directo"**
3. Clic derecho en el acceso directo → **"Propiedades"**
4. Clic en **"Cambiar icono..."**
5. Seleccionar un icono (o buscar uno en internet y guardarlo como .ico)

### Paso 3: (Opcional) Cambiar el nombre visible

El archivo se puede renombrar a algo más corto, por ejemplo:
- `Dashboard Mercado.bat`
- `Iniciar Dashboard.bat`
- `🚗 Dashboard.bat`

---

## 🎯 Cómo Usar

### Opción A: Doble clic (MÁS SIMPLE)

1. Hacer **doble clic** en `Iniciar_Dashboard_Mercado_Automotor.bat`
2. Se abrirán automáticamente 2 terminales:
   - **Terminal STREAMLIT** (fondo negro con texto cyan)
   - **Terminal NGROK** (fondo negro con texto amarillo)
3. Esperar unos segundos a que inicien
4. Ver instrucciones en pantalla

### Opción B: Ejecutar como Administrador (si hay problemas)

1. Clic derecho en `Iniciar_Dashboard_Mercado_Automotor.bat`
2. Seleccionar **"Ejecutar como administrador"**
3. Aceptar el prompt de UAC (Control de Cuentas de Usuario)

---

## 📊 Qué Verás al Ejecutar

### Terminal 1: STREAMLIT

```
====================================================================
  STREAMLIT - DASHBOARD MERCADO AUTOMOTOR
====================================================================

[+] Iniciando Streamlit...

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

✅ **Listo cuando veas:** "You can now view your Streamlit app"

### Terminal 2: NGROK

```
====================================================================
  NGROK - TUNEL PUBLICO
====================================================================

[+] Iniciando ngrok...

IMPORTANTE: Copia la URL que aparece en FORWARDING
Ejemplo: https://xxxx-xx-xx.ngrok-free.app

Session Status                online
Account                       tu_cuenta (Plan: Free)
Forwarding                    https://8fe8ba4c7e39.ngrok-free.app -> http://localhost:8501
```

✅ **Copiar esta URL:** `https://8fe8ba4c7e39.ngrok-free.app`

---

## 🌐 Acceder al Dashboard

### Para ti (LOCAL):
```
http://localhost:8501
```

### Para compartir (PÚBLICO):
```
https://8fe8ba4c7e39.ngrok-free.app
(La URL que aparece en la terminal de ngrok)
```

**Nota:** La URL de ngrok cambia cada vez que reinicias. Con cuenta gratuita es normal.

---

## 🛑 Cómo Detener

### Opción 1: Cerrar las terminales
- Hacer clic en la ❌ de cada ventana
- Confirmar si pregunta

### Opción 2: Ctrl+C en cada terminal
- Ir a cada terminal
- Presionar `Ctrl+C`
- Confirmar con `Y` si pregunta

### Opción 3: Matar procesos (si se cuelga)
```powershell
# En PowerShell:
# Matar Streamlit
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | Stop-Process -Force

# Matar ngrok
Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"} | Stop-Process -Force
```

---

## ⚙️ Personalizar el Script

Si necesitas cambiar rutas o puertos, edita el archivo .bat:

### Cambiar el directorio del proyecto:
```batch
REM Buscar esta línea:
cd C:\Users\juand\OneDrive\Escritorio\concecionaria\mercado_automotor

REM Cambiar por tu ruta:
cd C:\TU\RUTA\AQUI
```

### Cambiar el puerto de Streamlit:
```batch
REM Buscar:
streamlit run frontend/app_datos_gob.py

REM Cambiar por:
streamlit run frontend/app_datos_gob.py --server.port 8502
```

### Usar solo Streamlit (sin ngrok):
Editar el .bat y **comentar** la sección de ngrok:
```batch
REM Terminal 2: ngrok
REM start "NGROK..." powershell -NoExit -Command "..."
```

---

## 🔧 Troubleshooting

### Problema 1: "No se reconoce 'streamlit' como comando"

**Causa:** Python no está en el PATH o Streamlit no está instalado

**Solución:**
```powershell
# Instalar Streamlit
pip install streamlit

# O especificar ruta completa en el .bat:
python -m streamlit run frontend/app_datos_gob.py
```

### Problema 2: "No se reconoce 'ngrok' como comando"

**Causa:** ngrok no está en el PATH

**Solución A:** Agregar ngrok al PATH de Windows
1. Buscar donde está `ngrok.exe` (ej: `C:\ngrok\ngrok.exe`)
2. Agregar esa carpeta al PATH de Windows
3. Reiniciar PowerShell

**Solución B:** Especificar ruta completa en el .bat:
```batch
REM En lugar de:
ngrok http 8501

REM Usar:
C:\ruta\completa\ngrok.exe http 8501
```

### Problema 3: Las terminales se abren y cierran inmediatamente

**Causa:** Error en la ejecución de comandos

**Solución:** Ejecutar manualmente para ver el error:
```powershell
# En PowerShell:
cd C:\Users\juand\OneDrive\Escritorio\concecionaria\mercado_automotor
streamlit run frontend/app_datos_gob.py
```

Ver qué error da y resolverlo.

### Problema 4: PostgreSQL no está corriendo

**Síntoma:** Streamlit inicia pero dashboard muestra errores

**Solución:**
```powershell
# Si usas Docker:
docker-compose up -d postgres

# Si es servicio de Windows:
# Services.msc → PostgreSQL → Start
```

### Problema 5: El .bat no se ejecuta (se abre con editor de texto)

**Causa:** Windows está configurado para abrir .bat con editor

**Solución:**
1. Clic derecho en el .bat
2. Seleccionar **"Abrir con"**
3. Elegir **"Símbolo del sistema"** o **"Windows Command Processor"**
4. Marcar **"Usar siempre esta aplicación"**

---

## 📝 Contenido del Archivo .bat

El script hace lo siguiente:

```batch
1. Muestra mensaje de inicio
2. Abre terminal PowerShell con Streamlit
   - Navega a la carpeta del proyecto
   - Ejecuta: streamlit run frontend/app_datos_gob.py
3. Espera 5 segundos
4. Abre terminal PowerShell con ngrok
   - Ejecuta: ngrok http 8501
5. Muestra instrucciones
6. Se cierra automáticamente (las otras terminales quedan abiertas)
```

---

## 🎨 Personalización Avanzada

### Cambiar colores de las terminales:

Editar el .bat y agregar comandos de color:

```batch
start "STREAMLIT" powershell -NoExit -Command "$host.UI.RawUI.BackgroundColor = 'DarkBlue'; $host.UI.RawUI.ForegroundColor = 'White'; Clear-Host; cd ...; streamlit run ..."
```

### Agregar logs automáticos:

```batch
streamlit run frontend/app_datos_gob.py > streamlit_%date:~-4,4%%date:~-7,2%%date:~-10,2%.log 2>&1
```

### Minimizar terminales al iniciar:

```batch
start /MIN "STREAMLIT" powershell -NoExit -Command "..."
```

---

## ✅ Checklist de Verificación

Antes de usar el .bat, verificar:

- [ ] Python instalado y en PATH
- [ ] Streamlit instalado (`pip list | grep streamlit`)
- [ ] ngrok descargado y en PATH (o ruta completa en .bat)
- [ ] PostgreSQL corriendo
- [ ] Datos cargados en base de datos
- [ ] Ruta del proyecto correcta en el .bat

---

## 🔄 Actualizar el Script

Si haces cambios al .bat en el proyecto, recuerda actualizar la copia del escritorio:

```powershell
# Copiar versión actualizada al escritorio
copy C:\Users\juand\OneDrive\Escritorio\concecionaria\mercado_automotor\Iniciar_Dashboard_Mercado_Automotor.bat C:\Users\juand\Desktop\ /Y
```

---

## 📞 Soporte

Si hay problemas:

1. Verificar que ambos comandos funcionen manualmente:
   ```powershell
   streamlit run frontend/app_datos_gob.py
   ngrok http 8501
   ```

2. Revisar logs de error en las terminales

3. Consultar sección [Troubleshooting](#troubleshooting)

---

**¡El acceso directo está listo para usar!** 🚀

Simplemente haz doble clic en el archivo .bat y todo se iniciará automáticamente.
