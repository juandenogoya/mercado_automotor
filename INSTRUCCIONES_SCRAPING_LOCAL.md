# 🚗 Scraping DNRPA desde PC Local

Este script permite obtener datos de patentamientos desde la web oficial de DNRPA ejecutándolo desde tu **PC local** (con IP residencial), lo cual evita bloqueos de servidores cloud.

---

## 📋 Requisitos previos

### 1. Python instalado
- Verificar: Abrir terminal/cmd y ejecutar `python --version` o `python3 --version`
- Debe ser Python 3.7 o superior
- Si no está instalado: descargar de https://www.python.org/downloads/

### 2. Instalar dependencias

Abrir terminal/cmd en la carpeta del proyecto y ejecutar:

```bash
pip install requests beautifulsoup4 pandas openpyxl
```

O si usas `pip3`:

```bash
pip3 install requests beautifulsoup4 pandas openpyxl
```

---

## 🚀 Cómo ejecutar

### Opción 1: Desde la carpeta del proyecto

```bash
cd /ruta/a/mercado_automotor
python scraping_local_dnrpa.py
```

### Opción 2: Windows (doble click)

1. Descargar el archivo `scraping_local_dnrpa.py` a tu escritorio
2. Doble click en el archivo
3. Se abrirá una ventana de terminal mostrando el progreso

---

## 📊 Qué hace el script

1. **Conecta a DNRPA** usando tu IP residencial (evita bloqueos)
2. **Obtiene cookies** de sesión del servidor
3. **Envía formulario POST** con parámetros correctos
4. **Extrae tabla** con datos de patentamientos por provincia
5. **Guarda Excel** con el nombre `patentamientos_2024.xlsx`
6. **Muestra estadísticas** en pantalla

---

## 📈 Salida esperada

```
================================================================================
🚗 SCRAPING DNRPA - PATENTAMIENTOS
================================================================================
📅 Fecha: 2025-11-08 16:30:00
💻 Ejecutando desde: PC Local (IP residencial)
================================================================================

📊 Obteniendo datos de patentamientos para el año 2024...

📥 Paso 1/3: Cargando página inicial para obtener cookies...
   ✅ Status: 200
   🍪 Cookies recibidas: 2

📤 Paso 2/3: Enviando POST con datos del formulario...
   ✅ Status: 200

🔍 Paso 3/3: Parseando datos...
   📍 Provincias encontradas: 24
   ✅ Filas extraídas: 25

📈 DATOS OBTENIDOS:
================================================================================
Forma del DataFrame: (25, 14)

Primeras 5 provincias:
         Provincia / Mes   Ene   Feb   Mar   Abr   May   Jun   Jul   Ago   Sep   Oct   Nov   Dic  Total
0       BUENOS AIRES      10237  7366  7204  9572  8123  7891  8456  8922  9145  9876  8234  7654  102680
1  C.AUTONOMA DE BS.AS     6052  4680  4857  6410  5234  5123  5678  5432  5987  6234  5432  4876   65995
...

💾 Datos guardados en: patentamientos_2024.xlsx

📊 ESTADÍSTICAS:
================================================================================
Total de patentamientos 2024: 385,477

Top 5 provincias con más patentamientos:
  1. BUENOS AIRES: 102,680
  2. C.AUTONOMA DE BS.AS: 65,995
  3. CORDOBA: 45,234
  4. SANTA FE: 38,567
  5. MENDOZA: 22,345

================================================================================
✅ SCRAPING COMPLETADO EXITOSAMENTE
================================================================================
```

---

## ❌ Problemas comunes

### Error 403 - Acceso denegado

```
❌ ERROR: El servidor bloqueó la conexión con código 403
```

**Soluciones:**
1. Esperar 10-15 minutos y volver a intentar
2. Usar VPN con IP argentina
3. Verificar que DNRPA esté funcionando (abrir en navegador)
4. Contactar con el equipo para implementar Selenium

### Error de módulo no encontrado

```
ModuleNotFoundError: No module named 'requests'
```

**Solución:**
```bash
pip install requests beautifulsoup4 pandas openpyxl
```

### Timeout

```
❌ ERROR: Timeout al conectar con DNRPA
```

**Solución:**
- Verificar conexión a internet
- El servidor DNRPA puede estar caído temporalmente
- Reintentar en 5-10 minutos

---

## 📁 Archivos generados

| Archivo | Descripción |
|---------|-------------|
| `patentamientos_2024.xlsx` | Datos de patentamientos en formato Excel |
| `dnrpa_debug.html` | HTML de respuesta (solo si hay error) |

---

## 🔄 Próximos pasos

Una vez que obtengas el archivo Excel con éxito:

1. **Verificar datos** - Abrir `patentamientos_2024.xlsx` y revisar
2. **Cargar a BD** - Ejecutar script de carga a PostgreSQL
3. **Repetir para otros años** - Modificar variable `ANIO` en el script
4. **Automatizar** - Implementar Selenium + proxy para ejecución automática

---

## 🆘 Soporte

Si tienes problemas:

1. Verificar que el archivo `dnrpa_debug.html` se generó (contiene el HTML de respuesta)
2. Compartir el error completo que aparece en la terminal
3. Verificar que DNRPA funcione en tu navegador: https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/

---

## 📝 Notas técnicas

- **IP residencial**: Las IPs de casa suelen NO estar bloqueadas (a diferencia de cloud IPs)
- **Cookies**: El script obtiene cookies de sesión antes del POST
- **Headers**: Simula un navegador Chrome real
- **Formato números**: Convierte formato argentino (1.234) a número (1234)
- **SSL**: Deshabilita verificación SSL (sitio DNRPA puede tener certificado inválido)

---

**Última actualización**: 2025-11-08
