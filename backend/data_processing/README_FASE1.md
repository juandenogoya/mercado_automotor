# Fase 1: Preparación de Datos Transaccionales

## 📋 Objetivo

Unificar los datasets de **Inscripciones**, **Transferencias** y **Prendas** en un solo dataset optimizado para forecasting, con features temporales y agregadas.

---

## 🎯 ¿Qué hace esta fase?

1. ✅ **Explora** la estructura de las 3 tablas en PostgreSQL
2. ✅ **Verifica** compatibilidad de columnas
3. ✅ **Une** los 3 datasets en uno solo
4. ✅ **Agrega** columna `tipo_operacion` para identificar origen
5. ✅ **Crea** features temporales (año, mes, trimestre, día_semana, etc.)
6. ✅ **Crea** features agregadas (categorías, IDs, etc.)
7. ✅ **Guarda** en formato Parquet optimizado
8. ✅ **Valida** calidad de datos

---

## 📁 Archivos Creados

```
backend/data_processing/
├── 01_explorar_estructura_tablas.py    # Explora estructura de tablas PostgreSQL
├── 02_unir_datasets.py                 # Une datasets y crea features
├── 03_analisis_exploratorio.py         # Análisis estadístico del dataset unificado
└── README_FASE1.md                     # Esta documentación
```

---

## 🚀 Instrucciones de Uso

### **Paso 1: Verificar Requisitos**

Asegúrate de tener:
- PostgreSQL corriendo en `localhost:5432`
- Base de datos `mercado_automotor` con datos cargados
- Python 3.8+ con las siguientes librerías:
  ```bash
  pip install sqlalchemy pandas numpy pyarrow psycopg2-binary
  ```

### **Paso 2: Explorar Estructura de Tablas (Opcional)**

Este script te muestra las columnas de cada tabla y verifica compatibilidad:

```bash
# Desde el directorio raíz: mercado_automotor/
python backend/data_processing/01_explorar_estructura_tablas.py
```

**Salida esperada:**
- Lista de columnas por tabla
- Tipos de datos
- Total de registros
- Columnas comunes entre las 3 tablas

### **Paso 3: Unir Datasets y Crear Features** ⭐

Este es el script principal que genera el dataset unificado:

```bash
# Desde el directorio raíz: mercado_automotor/
python backend/data_processing/02_unir_datasets.py
```

**Lo que hace:**
1. Extrae datos de las 3 tablas: `datos_gob_inscripciones`, `datos_gob_transferencias`, `datos_gob_prendas`
2. Agrega columna `tipo_operacion` con valores: `'inscripcion'`, `'transferencia'`, `'prenda'`
3. Une los 3 datasets con `pd.concat()`
4. Ordena por `tramite_fecha`
5. Crea **features temporales**:
   - `anio`, `mes`, `dia`, `trimestre`
   - `dia_semana`, `dia_semana_nombre`
   - `semana_anio`, `mes_nombre`
   - `es_fin_semana`, `es_inicio_mes`, `es_fin_mes`
   - `mes_sin`, `mes_cos` (features cíclicas para estacionalidad)
   - `dia_semana_sin`, `dia_semana_cos`
   - `dias_desde_origen`
6. Crea **features agregadas**:
   - `operacion_id` (ID secuencial único)
   - `marca_categoria` (Top 10 marcas + "OTROS")
   - `tipo_categoria` (Top 10 tipos + "OTROS")
7. Guarda en **Parquet** (formato optimizado, compresión snappy)

**Archivos generados:**
```
data/processed/
├── dataset_transaccional_unificado.parquet       # Dataset completo (Parquet)
└── dataset_transaccional_unificado_sample.csv    # Muestra (primeros 1000 registros)
```

### **Paso 4: Análisis Exploratorio (Opcional)**

Analiza el dataset unificado generado:

```bash
# Desde el directorio raíz: mercado_automotor/
python backend/data_processing/03_analisis_exploratorio.py
```

**Lo que hace:**
- Estadísticas descriptivas
- Análisis temporal (mensual, anual, estacionalidad)
- Análisis por provincia
- Análisis de vehículos (marcas, tipos)
- Detección de outliers
- Resumen ejecutivo

---

## 📊 Dataset Unificado - Estructura

### **Columnas Principales**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `tramite_fecha` | datetime | Fecha de la operación |
| `tipo_operacion` | string | 'inscripcion', 'transferencia', 'prenda' |
| `registro_seccional_provincia` | string | Provincia del registro |
| `registro_seccional_descripcion` | string | Descripción del registro seccional |
| `automotor_origen` | string | Nacional/Importado |
| `automotor_marca_descripcion` | string | Marca del vehículo |
| `automotor_tipo_descripcion` | string | Tipo de vehículo (sedan, pick-up, etc.) |
| `automotor_modelo_descripcion` | string | Modelo del vehículo |
| `automotor_uso` | string | Particular/Comercial |
| `automotor_anio_modelo` | int | Año modelo del vehículo |

### **Features Temporales**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `anio` | int | Año de la operación |
| `mes` | int | Mes (1-12) |
| `dia` | int | Día del mes (1-31) |
| `trimestre` | int | Trimestre (1-4) |
| `dia_semana` | int | Día de la semana (0=Lunes, 6=Domingo) |
| `dia_semana_nombre` | string | Nombre del día |
| `semana_anio` | int | Semana del año (1-53) |
| `mes_nombre` | string | Nombre del mes |
| `es_fin_semana` | int | 1 si es sábado/domingo, 0 si no |
| `es_inicio_mes` | int | 1 si es día 1-7, 0 si no |
| `es_fin_mes` | int | 1 si es día 25+, 0 si no |
| `mes_sin` | float | sin(2π*mes/12) - estacionalidad cíclica |
| `mes_cos` | float | cos(2π*mes/12) - estacionalidad cíclica |
| `dia_semana_sin` | float | sin(2π*dia_semana/7) |
| `dia_semana_cos` | float | cos(2π*dia_semana/7) |
| `dias_desde_origen` | int | Días desde la primera operación |

### **Features Agregadas**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `operacion_id` | int | ID único secuencial |
| `marca_categoria` | string | Marca (Top 10) u "OTROS" |
| `tipo_categoria` | string | Tipo de vehículo (Top 10) u "OTROS" |

---

## 🔧 Configuración Avanzada

### **Limitar Registros para Testing**

Si querés probar con un subconjunto de datos (más rápido):

Editá `02_unir_datasets.py`, línea ~249:
```python
LIMIT = 10000  # Procesar solo 10,000 registros por tabla
```

### **Cambiar Formato de Salida**

Por defecto se guarda en **Parquet**. Si preferís CSV:

```python
# En lugar de:
df.to_parquet(filepath, index=False)

# Usar:
df.to_csv(filepath.replace('.parquet', '.csv'), index=False)
```

---

## 📈 Tamaño Esperado del Dataset

**Estimaciones (basadas en tablas actuales):**

| Tabla | Registros | Tamaño en Parquet |
|-------|-----------|-------------------|
| Inscripciones | ~3M | ~300 MB |
| Transferencias | ~9M | ~900 MB |
| Prendas | ~5M | ~500 MB |
| **TOTAL UNIFICADO** | **~17M** | **~1.5 GB** |

*Nota: Parquet con compresión snappy reduce tamaño ~60% vs CSV*

---

## ✅ Validación del Dataset

El script `02_unir_datasets.py` incluye validación automática:

- ✓ Total de registros por tipo de operación
- ✓ Rango temporal (fecha min/max)
- ✓ Distribución por provincia
- ✓ Distribución por marca
- ✓ Valores nulos por columna
- ✓ Registros por año

---

## 🐛 Troubleshooting

### Error: "Connection refused" (PostgreSQL)

**Problema:** PostgreSQL no está corriendo.

**Solución:**
```bash
# Windows (PowerShell como administrador)
net start postgresql-x64-15

# Verificar que esté corriendo
psql -U postgres -d mercado_automotor -c "SELECT 1"
```

### Error: "ModuleNotFoundError"

**Problema:** Falta instalar librerías.

**Solución:**
```bash
pip install sqlalchemy pandas numpy pyarrow psycopg2-binary
```

### Error: "Table does not exist"

**Problema:** Las tablas no están cargadas en PostgreSQL.

**Solución:**
```bash
# Cargar datos primero
python cargar_datos_gob_ar_postgresql.py
```

---

## 📊 Próximos Pasos (Fase 2)

Una vez que tengas el dataset unificado:

1. ✅ **Crear clientes de APIs** (BCRA, INDEC, CEM)
2. ✅ **Descargar datos macroeconómicos**
3. ✅ **Crear dataset macro** (IPC, TC, BADLAR, EMAE, etc.)
4. ✅ **Combinar datasets** (transaccional + macro) por fecha
5. ✅ **Feature engineering avanzado**
6. ✅ **Entrenar modelos de forecasting**

---

## 📝 Notas Importantes

- **Backup:** El script NO modifica las tablas originales en PostgreSQL
- **Idempotencia:** Podés ejecutar los scripts múltiples veces
- **Memoria:** Procesamiento de ~17M registros requiere ~8-16 GB RAM
- **Tiempo:** Ejecución completa: ~10-20 minutos (depende del hardware)

---

## 🆘 Ayuda

Si tenés problemas, verificá:

1. PostgreSQL está corriendo (`psql -U postgres -l`)
2. Las tablas tienen datos (`SELECT COUNT(*) FROM datos_gob_inscripciones`)
3. Tenés suficiente espacio en disco (~2 GB libres)
4. Las librerías están instaladas (`pip list | grep pandas`)

---

## 📧 Contacto

Para bugs o mejoras, reportar en el repositorio del proyecto.

---

**Fecha:** 2025-11-12
**Versión:** 1.0
**Autor:** Claude + Usuario
