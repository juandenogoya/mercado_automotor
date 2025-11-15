# 🚀 Cómo Crear Acceso Directo en el Escritorio

## Método 1: Crear acceso directo manualmente

1. **Clic derecho** en el archivo `Iniciar_Dashboard_Mercado_Automotor.bat`
2. Seleccionar **"Enviar a" → "Escritorio (crear acceso directo)"**
3. ¡Listo! Ahora tenés el acceso directo en tu escritorio

## Método 2: Crear acceso directo personalizado

1. **Clic derecho** en el escritorio → **Nuevo → Acceso directo**
2. En **"Ubicación del elemento"**, poner:
   ```
   C:\Users\juand\OneDrive\Escritorio\concecionaria\mercado_automotor\Iniciar_Dashboard_Mercado_Automotor.bat
   ```
   (Ajustar la ruta si tu proyecto está en otro lugar)

3. Click en **"Siguiente"**
4. Nombrar el acceso directo: **"Dashboard Mercado Automotor"**
5. Click en **"Finalizar"**

### Personalizar el ícono (opcional):

6. **Clic derecho** en el acceso directo → **"Propiedades"**
7. Click en **"Cambiar icono"**
8. Elegir un ícono o buscar online un ícono de auto/dashboard (.ico)
9. Click en **"Aceptar"**

---

## 📋 Qué hace el script automáticamente:

Cuando ejecutás el `.bat`, automáticamente:

### ✅ **[0/5] Verificación de Entorno Virtual**
- Detecta si existe `venv` y lo usa automáticamente
- Si no existe, usa Python del sistema

### ✅ **[1/5] Actualización de Datos Externos**
- Ejecuta `actualizar_datos_externos.py`
- Actualiza BADLAR, IPC, Tipo de Cambio desde BCRA e INDEC
- Muestra [OK] si fue exitoso o [ADVERTENCIA] si hubo problemas

### ✅ **[2/5] Revisión de Datos Nuevos**
- Busca archivos CSV nuevos en carpetas `INPUT/`:
  - `INPUT/INSCRIPCIONES/*.csv`
  - `INPUT/TRANSFERENCIAS/*.csv`
  - `INPUT/PRENDAS/*.csv`
- Si encuentra archivos:
  - Te pregunta si querés procesarlos ahora
  - Opción S: Los carga a PostgreSQL automáticamente
  - Opción N: Los omite y continúa

### ✅ **[3/5] Abre Streamlit**
- Abre una terminal PowerShell con Streamlit
- Activa el entorno virtual automáticamente
- Ejecuta `streamlit run frontend/app_datos_gob.py`
- Dashboard disponible en: http://localhost:8501

### ✅ **[4/5] Abre ngrok**
- Abre una terminal PowerShell con ngrok
- Crea un túnel público a tu Streamlit local
- Muestra la URL pública para compartir (ej: `https://xxxx.ngrok-free.app`)

---

## 🎯 URLs que obtendrás:

| Acceso | URL | Para quién |
|--------|-----|------------|
| **Local** | http://localhost:8501 | Solo vos en tu PC |
| **Pública (ngrok)** | https://xxxx-xx-xx.ngrok-free.app | Cualquiera con la URL (compartible) |

---

## 🛑 Para detener todo:

1. **Cerrar las ventanas** de PowerShell (Streamlit y ngrok)
   O
2. Presionar **Ctrl+C** en cada ventana de PowerShell

---

## ⚠️ Requisitos previos:

### Python y dependencias:
```powershell
pip install streamlit pandas plotly sqlalchemy psycopg2-binary
```

### ngrok:
**Opción 1 (con Chocolatey):**
```powershell
choco install ngrok
```

**Opción 2 (manual):**
1. Descargar de: https://ngrok.com/download
2. Extraer `ngrok.exe` a una carpeta en PATH
3. Autenticarse: `ngrok authtoken TU_TOKEN`
   (Obtener token gratis en: https://dashboard.ngrok.com/get-started/your-authtoken)

---

## 🔧 Solución de problemas:

### Error: "Python no reconocido"
→ Instalar Python o agregar Python al PATH

### Error: "Streamlit no reconocido"
→ Ejecutar: `pip install streamlit`

### Error: "ngrok no reconocido"
→ Instalar ngrok (ver arriba)

### Error: "No se puede conectar a PostgreSQL"
→ Verificar que PostgreSQL esté corriendo
→ Verificar credenciales en `.env`

---

## 💡 Consejos:

1. **Primera vez**: Ejecutá el .bat desde la carpeta del proyecto para verificar que todo funcione
2. **ngrok gratuito**: Tiene un límite de 40 conexiones/minuto
3. **Actualizar datos**: El script pregunta si querés procesar CSVs nuevos cada vez
4. **Variables macro**: Se actualizan automáticamente de BCRA/INDEC al inicio

---

¿Problemas? Revisá los logs en las ventanas de PowerShell que se abren.
