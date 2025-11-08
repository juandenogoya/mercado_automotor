# 🇦🇷 Guía de uso de API datos.gob.ar

Esta guía explica cómo explorar y consumir datos del portal oficial de datos abiertos de Argentina.

---

## 📋 Scripts disponibles

### 1️⃣ **explorar_datasets_gob_ar.py**
Busca datasets relacionados con el mercado automotor.

**Uso:**
```bash
python explorar_datasets_gob_ar.py
```

**Qué hace:**
- Busca datasets por palabras clave (automotor, patentamiento, vehículo, INDEC, etc.)
- Elimina duplicados
- Guarda resultados en `datasets_encontrados.json`
- Muestra datasets más relevantes

**Salida esperada:**
```
🔍 EXPLORADOR DE DATASETS - datos.gob.ar
================================================================================

📌 Buscando: 'automotor'...
   ✅ 12 datasets encontrados

📌 Buscando: 'patentamiento'...
   ✅ 8 datasets encontrados

...

📊 RESUMEN: 25 datasets únicos encontrados
================================================================================

📋 DATASETS ENCONTRADOS:

1. Estadística de trámites de automotores
   ID: justicia-estadistica-tramites-automotores
   Organización: Ministerio de Justicia
   Keyword: automotor

...
```

---

### 2️⃣ **explorar_dataset_detalle.py**
Explora los detalles y recursos de un dataset específico.

**Uso:**
```bash
python explorar_dataset_detalle.py --id <dataset_id>
```

**Ejemplo:**
```bash
python explorar_dataset_detalle.py --id justicia-estadistica-tramites-automotores
```

**Qué hace:**
- Obtiene información detallada del dataset
- Lista todos los recursos/archivos disponibles
- Muestra formato, URL, tamaño
- Genera comandos de descarga
- Guarda recursos en JSON

**Salida esperada:**
```
🔍 EXPLORADOR DE DATASET - datos.gob.ar
================================================================================

📋 INFORMACIÓN GENERAL
================================================================================

📌 Título: Estadística de trámites de automotores
🆔 ID: justicia-estadistica-tramites-automotores
🏢 Organización: Ministerio de Justicia
...

📦 RECURSOS DISPONIBLES (15)
================================================================================

1. Patentamientos por provincia 2020
   📄 Formato: CSV
   🔗 URL: https://datos.gob.ar/dataset/...
   💾 DESCARGABLE - Comando:
      wget 'https://...' -O datos.csv

...

📊 ANÁLISIS DE FORMATOS
================================================================================
  CSV: 10 archivo(s)
  JSON: 3 archivo(s)
  XLSX: 2 archivo(s)
```

---

## 🚀 Workflow completo

### Paso 1: Explorar datasets disponibles
```bash
python explorar_datasets_gob_ar.py
```

Esto genera `datasets_encontrados.json` con todos los datasets relevantes.

### Paso 2: Examinar un dataset específico
```bash
python explorar_dataset_detalle.py --id justicia-estadistica-tramites-automotores
```

Esto genera `dataset_justicia-estadistica-tramites-automotores_recursos.json` con los recursos.

### Paso 3: Descargar datos
Usar los comandos `wget` generados, o crear un script personalizado.

### Paso 4: Cargar a PostgreSQL
Crear un script de carga específico para ese dataset.

### Paso 5: Actualizar dashboard
Agregar visualizaciones en Streamlit.

---

## 📊 Datasets relevantes conocidos

### 🚗 Estadística de trámites de automotores
- **ID:** `justicia-estadistica-tramites-automotores`
- **Fuente:** Ministerio de Justicia / DNRPA
- **Contenido:** Inscripciones, transferencias por provincia
- **Formato:** CSV comprimidos
- **Actualización:** Mensual
- **Desde:** Enero 2000

### 📈 Índices de patentamientos
- **ID:** (buscar con el explorador)
- **Fuente:** INDEC
- **Contenido:** Índices trimestrales
- **Formato:** PDF, XLS

### 🏭 Producción automotriz
- **ID:** (buscar con el explorador)
- **Fuente:** Ministerio de Producción
- **Contenido:** Producción, exportación, importación
- **Formato:** CSV

---

## 🔧 API de datos.gob.ar

### Base URL
```
https://datos.gob.ar/api/3
```

### Endpoints principales

#### Buscar datasets
```
GET /action/package_search?q=<query>&rows=<limit>
```

#### Obtener dataset por ID
```
GET /action/package_show?id=<dataset_id>
```

#### Listar organizaciones
```
GET /action/organization_list
```

#### Listar grupos/categorías
```
GET /action/group_list
```

---

## 📝 Estructura de respuesta

### Dataset
```json
{
  "success": true,
  "result": {
    "id": "dataset-id",
    "title": "Título del dataset",
    "notes": "Descripción",
    "organization": {
      "title": "Organización",
      "name": "org-name"
    },
    "tags": [
      {"display_name": "automotor"},
      {"display_name": "patentamiento"}
    ],
    "resources": [
      {
        "id": "resource-id",
        "name": "Nombre del recurso",
        "format": "CSV",
        "url": "https://...",
        "size": 1234567,
        "mimetype": "text/csv"
      }
    ]
  }
}
```

---

## 💡 Tips

### Búsqueda efectiva
- Usar palabras clave específicas
- Probar variaciones (automotor, automotriz, vehículo)
- Buscar por organización (INDEC, Justicia, Producción)

### Formatos preferidos
- **CSV**: Fácil de parsear, ideal para PostgreSQL
- **JSON**: Directo a aplicación
- **XLSX**: Requiere pandas, pero muy común

### Actualización de datos
- Verificar `metadata_modified` del dataset
- Algunos se actualizan mensualmente, otros trimestralmente
- Automatizar con cron jobs

---

## 🎯 Próximos pasos

1. **Ejecutar exploradores** para encontrar datasets relevantes
2. **Identificar los más útiles** para el proyecto
3. **Crear scripts de descarga** automática
4. **Parsear y normalizar** datos
5. **Cargar a PostgreSQL**
6. **Integrar al dashboard**

---

## 📚 Recursos

- **Portal:** https://datos.gob.ar
- **Documentación API:** https://datos.gob.ar/acerca/seccion/developers
- **CKAN API Docs:** https://docs.ckan.org/en/latest/api/

---

**Última actualización:** 2025-11-08
