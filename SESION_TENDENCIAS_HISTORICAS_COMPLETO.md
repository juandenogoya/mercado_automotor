# SESIÓN: Agregado de Pestaña Tendencias Históricas (2007-2025)

**Fecha:** 11 de Noviembre de 2025
**Branch Principal:** `claude/continue-project-011CUzjS5wAvCY8xCtvfzV16`
**Estado:** ✅ COMPLETADO Y FUNCIONAL

---

## 📋 ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Contexto Inicial](#contexto-inicial)
3. [Problema Identificado](#problema-identificado)
4. [Solución Implementada](#solución-implementada)
5. [Arquitectura Técnica](#arquitectura-técnica)
6. [Archivos Creados/Modificados](#archivos-creados-modificados)
7. [Estado de las Branches](#estado-de-las-branches)
8. [Base de Datos](#base-de-datos)
9. [Instrucciones de Uso](#instrucciones-de-uso)
10. [Próximos Pasos Sugeridos](#próximos-pasos-sugeridos)
11. [Troubleshooting](#troubleshooting)
12. [Comandos Útiles](#comandos-útiles)

---

## 📊 RESUMEN EJECUTIVO

### ¿Qué se logró?

Se agregó una nueva pestaña al dashboard de Streamlit llamada **"📊 Tendencias Históricas"** que permite analizar estadísticas agregadas mensuales de trámites automotores desde **2007 hasta 2025**.

### Diferencias clave con datos existentes:

| **Datos Detallados (PostgreSQL existente)** | **Datos Agregados (NUEVO)** |
|----------------------------------------------|------------------------------|
| 1 fila = 1 trámite individual | 1 fila = total mes/provincia |
| 13.6M registros, 4.92 GB | ~18K registros, 0.84 MB |
| Incluye: marca, modelo, género, edad | Solo: cantidad por mes/provincia |
| Desde 2019 | **Desde 2007** |
| Solo autos/motos | Incluye **Maquinarias** |
| Consultas lentas | **Consultas súper rápidas** |

### Métricas del Resultado:

- ✅ **8,928** registros de inscripciones cargados
- ✅ **8,916** registros de transferencias cargados
- ✅ **6 visualizaciones** interactivas creadas
- ✅ **4 filtros** dinámicos implementados
- ✅ **19 años** de datos históricos (2007-2025)
- ✅ **2 tipos** de vehículos: Motovehículos y Maquinarias

---

## 🎯 CONTEXTO INICIAL

### Estado del Proyecto antes de la Sesión:

El dashboard `frontend/app_datos_gob.py` tenía **5 pestañas**:

1. 🚗 Inscripciones
2. 🔄 Transferencias
3. 💰 Prendas
4. 📍 Registros Seccionales
5. 🔬 Análisis Detallado

Todas estas pestañas trabajaban con datos **detallados** (cada fila = 1 trámite) almacenados en tablas:
- `datos_gob_inscripciones` (2.97M registros, 1.08 GB)
- `datos_gob_transferencias` (8.83M registros, 3.15 GB)
- `datos_gob_prendas` (1.79M registros, 617 MB)

**Limitaciones identificadas:**
- Datos solo desde 2019
- No incluía sector "Maquinarias"
- Consultas lentas por volumen de datos
- Sin análisis histórico de largo plazo

### Solicitud del Usuario:

El usuario agregó 4 archivos CSV con **datos agregados mensuales** y solicitó:

1. Analizar estos nuevos archivos
2. Cargarlos a PostgreSQL
3. Crear visualizaciones en el dashboard
4. Mantener estructura similar a las pestañas existentes
5. Considerar que los nombres de archivos cambiarán mensualmente

**Archivos proporcionados:**
```
INPUT/INSCRIPCIONES/estadistica-inscripciones-iniciales-motovehiculos-2007-01-2025-09.csv (0.27 MB)
INPUT/INSCRIPCIONES/estadistica-inscripciones-iniciales-maquinarias-2013-09-2025-09.csv (0.16 MB)
INPUT/TRANSFERENCIAS/estadistica-transferencias-motovehiculos-2007-01-2025-09.csv (0.26 MB)
INPUT/TRANSFERENCIAS/estadistica-transferencias-maquinarias-2013-09-2025-09.csv (0.15 MB)
```

---

## 🔍 PROBLEMA IDENTIFICADO

### 1. **Estructura de los datos:**
Los CSV tienen estructura agregada (1 fila = total mes/provincia):
```csv
"tipo_vehiculo","anio_inscripcion_inicial","mes_inscripcion_inicial","provincia_inscripcion_inicial","letra_provincia_inscripcion_inicial","cantidad_inscripciones_iniciales","provincia_id"
"Motovehículos",2007,1,"Buenos Aires","B",8867,"06"
```

### 2. **Nombres dinámicos de archivos:**
Los archivos cambian mensualmente:
- `estadistica-transferencias-motovehiculos-2007-01-2025-09.csv` (septiembre 2025)
- `estadistica-transferencias-motovehiculos-2007-01-2025-10.csv` (octubre 2025)

Se necesitaba un script **flexible** que detecte automáticamente los archivos más recientes.

### 3. **Integración con PostgreSQL existente:**
Requerimiento de mantener la misma estructura de acceso a datos que las otras pestañas del dashboard.

---

## ✅ SOLUCIÓN IMPLEMENTADA

### Componentes Creados:

#### 1. **Tablas PostgreSQL**
Se crearon 2 nuevas tablas para datos agregados:

**Archivo:** `sql/crear_tablas_estadisticas_agregadas.sql`

```sql
CREATE TABLE estadisticas_inscripciones (
    id SERIAL PRIMARY KEY,
    tipo_vehiculo VARCHAR(50) NOT NULL,
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes >= 1 AND mes <= 12),
    provincia VARCHAR(100) NOT NULL,
    letra_provincia VARCHAR(1),
    provincia_id VARCHAR(2),
    cantidad INTEGER NOT NULL DEFAULT 0,
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archivo_origen VARCHAR(255),
    CONSTRAINT uk_estadisticas_inscripciones UNIQUE (tipo_vehiculo, anio, mes, provincia)
);

CREATE TABLE estadisticas_transferencias (
    -- Misma estructura
);
```

**Características:**
- ✅ Constraint UNIQUE para evitar duplicados
- ✅ Índices en `anio`, `mes`, `provincia`, `tipo_vehiculo`
- ✅ Campo `archivo_origen` para auditoría
- ✅ Vistas para totales nacionales y rankings

#### 2. **Script de Carga Flexible**

**Archivo:** `cargar_estadisticas_agregadas.py`

**Funcionalidades:**
- 🔍 Busca automáticamente archivos CSV con patrones:
  - `estadistica-inscripciones-iniciales-motovehiculos-*.csv`
  - `estadistica-inscripciones-iniciales-maquinarias-*.csv`
  - `estadistica-transferencias-motovehiculos-*.csv`
  - `estadistica-transferencias-maquinarias-*.csv`

- 📅 Selecciona el archivo más reciente si hay múltiples versiones
- 🔄 Inserción incremental con `ON CONFLICT DO UPDATE`
- ✅ Elimina BOM (Byte Order Mark) automáticamente
- 📊 Muestra progreso y estadísticas de carga

**Ejemplo de uso:**
```bash
python cargar_estadisticas_agregadas.py
```

**Output esperado:**
```
================================================================================
CARGA DE ESTADISTICAS AGREGADAS
================================================================================

1. Creando tablas...
Tablas creadas OK

2. Buscando archivos CSV...
Encontrado (inscripciones_motovehiculos): estadistica-inscripciones-iniciales-motovehiculos-2007-01-2025-09.csv
Encontrado (inscripciones_maquinarias): estadistica-inscripciones-iniciales-maquinarias-2013-09-2025-09.csv
Encontrado (transferencias_motovehiculos): estadistica-transferencias-motovehiculos-2007-01-2025-09.csv
Encontrado (transferencias_maquinarias): estadistica-transferencias-maquinarias-2013-09-2025-09.csv

3. Cargando datos...
Procesados: 5424 registros
Procesados: 3504 registros
Procesados: 5424 registros
Procesados: 3492 registros

4. Verificando datos cargados...
  Inscripciones: 8,928 registros
  Transferencias: 8,916 registros

================================================================================
COMPLETADO
================================================================================
```

#### 3. **Nueva Pestaña en Dashboard**

**Archivo modificado:** `frontend/app_datos_gob.py`

**Línea 98:** Se agregó `tab6`:
```python
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🚗 Inscripciones",
    "🔄 Transferencias",
    "💰 Prendas",
    "📍 Registros Seccionales",
    "🔬 Análisis Detallado",
    "📊 Tendencias Históricas"  # NUEVA
])
```

**Líneas 1144-1431:** Implementación completa de la pestaña

---

## 🏗️ ARQUITECTURA TÉCNICA

### Flujo de Datos:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. ORIGEN: datos.gob.ar                                        │
│     Estadísticas agregadas mensuales CSV                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. DESCARGA MANUAL                                             │
│     Usuario descarga CSV y los coloca en:                       │
│     data/estadisticas_dnrpa/                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. SCRIPT DE CARGA                                             │
│     cargar_estadisticas_agregadas.py                            │
│     - Detecta archivos más recientes                            │
│     - Limpia BOM                                                │
│     - Mapea columnas                                            │
│     - Inserta/actualiza en PostgreSQL                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. POSTGRESQL                                                  │
│     Tablas:                                                     │
│     - estadisticas_inscripciones (8,928 registros)             │
│     - estadisticas_transferencias (8,916 registros)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. DASHBOARD STREAMLIT                                         │
│     frontend/app_datos_gob.py                                   │
│     Pestaña "Tendencias Históricas"                             │
│     - Filtros dinámicos                                         │
│     - Consultas SQL optimizadas                                 │
│     - Visualizaciones Plotly                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. VISUALIZACIÓN                                               │
│     - Serie temporal 2007-2025                                  │
│     - Top 10 provincias                                         │
│     - Estacionalidad                                            │
│     - Heatmap                                                   │
│     - Tablas interactivas                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico:

- **Backend:** Python 3.11+
- **Framework Web:** Streamlit 1.28.2
- **Base de Datos:** PostgreSQL (con tablas TimescaleDB)
- **ORM:** SQLAlchemy 1.4.x
- **Visualizaciones:** Plotly Express 5.18.0
- **Procesamiento Datos:** Pandas 2.1.3
- **Deployment Local:** ngrok (para compartir)

---

## 📁 ARCHIVOS CREADOS/MODIFICADOS

### Archivos CREADOS:

#### 1. `sql/crear_tablas_estadisticas_agregadas.sql`
**Propósito:** Definición de esquema PostgreSQL
**Líneas:** 180
**Contenido:**
- Tablas `estadisticas_inscripciones` y `estadisticas_transferencias`
- 8 índices optimizados
- 4 vistas SQL para análisis
- Comentarios y documentación

#### 2. `cargar_estadisticas_agregadas.py`
**Propósito:** Script de carga de datos
**Líneas:** 180
**Funciones principales:**
- `encontrar_archivos_csv()`: Detecta archivos más recientes
- `limpiar_bom()`: Elimina BOM de columnas
- `cargar_csv_a_dataframe()`: Lee y prepara CSV
- `mapear_columnas_*()`: Adapta nombres de columnas
- `main()`: Orquesta el proceso completo

#### 3. `INSTRUCCIONES_ESTADISTICAS_AGREGADAS.md`
**Propósito:** Documentación de uso
**Líneas:** 166
**Secciones:**
- Qué son los datos agregados
- Instrucciones paso a paso
- Actualización mensual
- Verificación de datos
- Troubleshooting

#### 4. `data/estadisticas_dnrpa/*.csv` (4 archivos)
**Propósito:** Datos fuente
**Tamaño total:** 0.84 MB
**Archivos:**
- `estadistica-inscripciones-iniciales-motovehiculos-2007-01-2025-09.csv` (0.27 MB, 5,425 filas)
- `estadistica-inscripciones-iniciales-maquinarias-2013-09-2025-09.csv` (0.16 MB, 3,505 filas)
- `estadistica-transferencias-motovehiculos-2007-01-2025-09.csv` (0.26 MB, 5,425 filas)
- `estadistica-transferencias-maquinarias-2013-09-2025-09.csv` (0.15 MB, 3,493 filas)

### Archivos MODIFICADOS:

#### 1. `frontend/app_datos_gob.py`
**Cambios:**
- **Línea 98:** Agregado `tab6` a la declaración de pestañas
- **Líneas 1144-1431:** Implementación completa de pestaña "Tendencias Históricas" (287 líneas nuevas)

**Estructura de la nueva pestaña:**
```python
with tab6:
    # 1. Header y verificación de tablas
    # 2. Filtros (tipo vehículo, tipo trámite, años, provincias)
    # 3. Consulta SQL principal
    # 4. Métricas generales (4 cards)
    # 5. Gráfico: Serie temporal nacional
    # 6. Gráfico: Top 10 provincias
    # 7. Gráfico: Estacionalidad por mes
    # 8. Gráfico: Evolución anual
    # 9. Gráfico: Heatmap estacional
    # 10. Tabla de datos detallados (expandible)
```

---

## 🌿 ESTADO DE LAS BRANCHES

### Branch Principal (ACTIVA):
```
claude/continue-project-011CUzjS5wAvCY8xCtvfzV16
```
**Estado:** ✅ Todo funcionando y pusheado
**Último commit:** `aae6df5` - "feat: Agregar pestaña Tendencias Históricas con datos agregados 2007-2025"
**Archivos incluidos:**
- ✅ `sql/crear_tablas_estadisticas_agregadas.sql`
- ✅ `cargar_estadisticas_agregadas.py`
- ✅ `INSTRUCCIONES_ESTADISTICAS_AGREGADAS.md`
- ✅ `data/estadisticas_dnrpa/*.csv` (4 archivos)
- ✅ `frontend/app_datos_gob.py` (modificado)

### Branch Secundaria (USADA TEMPORALMENTE):
```
desarrollo/dashboard-datos-gob-2025
```
**Estado:** ⚠️ Tiene 3 commits sin pushear (problema de permisos 403)
**Uso:** Se usó temporalmente porque el usuario ya estaba trabajando ahí
**Resolución:** Se trasladaron todos los cambios a la branch principal `claude/continue-project-011CUzjS5wAvCY8xCtvfzV16`

### Otras Branches:
```
main                                              # Branch principal del repo (sin tocar)
claude/review-project-advantages-011CUvWjZ32...   # Branch de revisión anterior
claude/sync-dashboard-detallado-011CUzjS5wAvC...  # Branch anterior de desarrollo
```

### Diagrama de Branches:

```
main
  │
  ├─── desarrollo/dashboard-datos-gob-2025
  │         │
  │         ├─ (Trabajo temporal del usuario)
  │         └─ (3 commits sin pushear - problema 403)
  │
  └─── claude/continue-project-011CUzjS5wAvCY8xCtvfzV16 ✅
            │
            ├─ commit 557f0b3: Infraestructura estadísticas agregadas
            ├─ commit dfa3850: Documentación
            └─ commit aae6df5: Nueva pestaña dashboard (ACTUAL)
```

---

## 🗄️ BASE DE DATOS

### Estado Actual de PostgreSQL:

```sql
-- Base de datos: mercado_automotor
-- Tamaño total: 4.92 GB
-- Total registros: 13,618,228

-- Tablas existentes (datos detallados):
datos_gob_inscripciones       -- 2,970,063 registros, 1.08 GB
datos_gob_transferencias      -- 8,834,929 registros, 3.15 GB
datos_gob_prendas             -- 1,793,747 registros, 617 MB
datos_gob_registros_seccionales -- 1,561 registros, 24 MB

-- Tablas NUEVAS (datos agregados):
estadisticas_inscripciones    -- 8,928 registros, <1 MB ✅
estadisticas_transferencias   -- 8,916 registros, <1 MB ✅
```

### Verificación de Datos Cargados:

```sql
-- Total de registros por tabla
SELECT COUNT(*) FROM estadisticas_inscripciones;
-- Resultado esperado: 8,928

SELECT COUNT(*) FROM estadisticas_transferencias;
-- Resultado esperado: 8,916

-- Rango de años disponibles
SELECT
    tipo_vehiculo,
    MIN(anio) as primer_anio,
    MAX(anio) as ultimo_anio,
    COUNT(DISTINCT anio) as total_anios
FROM estadisticas_inscripciones
GROUP BY tipo_vehiculo;

-- Resultado esperado:
-- Motovehículos: 2007-2025 (19 años)
-- Maquinarias: 2013-2025 (13 años)

-- Top 5 provincias con más trámites históricos
SELECT
    provincia,
    SUM(cantidad) as total
FROM estadisticas_inscripciones
WHERE tipo_vehiculo = 'Motovehículos'
GROUP BY provincia
ORDER BY total DESC
LIMIT 5;
```

### Índices Creados:

```sql
-- Inscripciones
idx_est_inscripciones_anio_mes       -- Para filtros temporales
idx_est_inscripciones_provincia      -- Para filtros geográficos
idx_est_inscripciones_tipo           -- Para filtros por tipo vehículo
idx_est_inscripciones_anio_tipo      -- Para consultas combinadas

-- Transferencias (misma estructura)
idx_est_transferencias_anio_mes
idx_est_transferencias_provincia
idx_est_transferencias_tipo
idx_est_transferencias_anio_tipo
```

### Vistas SQL Creadas:

```sql
-- Vista: Totales nacionales mensuales
vista_totales_mensuales_inscripciones
vista_totales_mensuales_transferencias

-- Vista: Ranking provincial histórico
vista_ranking_provincial_inscripciones
vista_ranking_provincial_transferencias
```

---

## 📖 INSTRUCCIONES DE USO

### Para Iniciar el Dashboard:

```powershell
# 1. Navegar al directorio del proyecto
cd C:\Users\juand\OneDrive\Escritorio\concecionaria\mercado_automotor

# 2. Asegurarse de estar en la branch correcta
git branch
# Debe mostrar: * claude/continue-project-011CUzjS5wAvCY8xCtvfzV16

# 3. Iniciar Streamlit
streamlit run frontend/app_datos_gob.py

# 4. Abrir navegador en: http://localhost:8501
```

### Para Compartir con ngrok:

```powershell
# Terminal 1: Streamlit (debe estar corriendo)
streamlit run frontend/app_datos_gob.py

# Terminal 2: ngrok
ngrok http 8501

# Copiar la URL generada (ej: https://xxxx.ngrok-free.app)
# Compartir con el usuario
```

### Para Actualizar Datos Mensualmente:

```powershell
# 1. Descargar nuevos CSV desde datos.gob.ar
# Ejemplo: estadistica-inscripciones-iniciales-motovehiculos-2007-01-2025-10.csv

# 2. Colocar en: data/estadisticas_dnrpa/

# 3. Ejecutar script de carga
python cargar_estadisticas_agregadas.py

# El script automáticamente:
# - Detecta los archivos más recientes
# - Actualiza solo registros modificados
# - Evita duplicados

# 4. Reiniciar Streamlit si está corriendo
# Ctrl+C en la terminal de Streamlit
# streamlit run frontend/app_datos_gob.py
```

### Para Verificar Funcionamiento:

```powershell
# 1. Abrir dashboard
# 2. Hacer clic en pestaña "📊 Tendencias Históricas"
# 3. Verificar que aparezcan:
#    - Filtros: Tipo Vehículo, Tipo Trámite, Años, Provincias
#    - 4 métricas en cards
#    - 5-6 gráficos interactivos
# 4. Probar cambiar filtros y ver que los gráficos se actualicen
```

---

## 🔮 PRÓXIMOS PASOS SUGERIDOS

### Corto Plazo (1-2 semanas):

#### 1. **Comparativa con Datos Detallados**
**Prioridad:** Media
**Complejidad:** Baja
**Descripción:** Agregar gráfico que compare totales de:
- Datos agregados (estadisticas_inscripciones)
- Datos detallados (datos_gob_inscripciones)

Para validar consistencia entre ambas fuentes.

**Implementación sugerida:**
```python
# En la pestaña Tendencias Históricas, agregar:
with st.expander("🔍 Validación con Datos Detallados"):
    # Consulta datos agregados
    query_agregados = "SELECT SUM(cantidad) FROM estadisticas_inscripciones WHERE anio >= 2019"

    # Consulta datos detallados
    query_detallados = "SELECT COUNT(*) FROM datos_gob_inscripciones"

    # Mostrar comparación
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Datos Agregados", total_agregados)
    with col2:
        st.metric("Datos Detallados", total_detallados)
```

#### 2. **Exportación de Datos**
**Prioridad:** Alta
**Complejidad:** Baja
**Descripción:** Permitir descargar datos filtrados en formato:
- CSV
- Excel
- PDF (resumen)

**Implementación sugerida:**
```python
import io

# Botón de descarga
csv = df_hist.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descargar datos (CSV)",
    data=csv,
    file_name=f'tendencias_{tipo_tramite_hist}_{tipo_vehiculo_hist}.csv',
    mime='text/csv'
)
```

#### 3. **Comparación entre Provincias**
**Prioridad:** Media
**Complejidad:** Media
**Descripción:** Agregar gráfico de líneas que permita comparar evolución temporal de múltiples provincias en el mismo gráfico.

**Mockup:**
```python
# Gráfico de líneas múltiples
fig = px.line(
    df_provincias_comparacion,
    x='fecha',
    y='total',
    color='provincia',
    title='Comparación entre Provincias Seleccionadas'
)
```

### Mediano Plazo (1-2 meses):

#### 4. **Deployment Permanente**
**Prioridad:** Alta (si se quiere compartir permanentemente)
**Complejidad:** Alta
**Opciones:**

**Opción A: Streamlit Cloud + Supabase (GRATIS)**
- Filtrar datos a 2023-2025 (reducir a ~500MB)
- Migrar PostgreSQL a Supabase (500 MB free tier)
- Deploy dashboard en Streamlit Cloud (gratis)
- **Costo:** $0/mes

**Opción B: Streamlit Cloud + Neon (GRATIS hasta 3GB)**
- Filtrar datos a 2020-2025 (reducir a ~1.5GB)
- Migrar PostgreSQL a Neon (3 GB free tier)
- Deploy dashboard en Streamlit Cloud (gratis)
- **Costo:** $0/mes

**Opción C: Cloud Completo (PAGO)**
- Mantener todos los datos (4.92 GB)
- Neon PostgreSQL: $19/mes (10 GB)
- Streamlit Cloud: gratis
- **Costo:** $19/mes

**Documentación necesaria:**
- Guía de migración PostgreSQL → Cloud
- Configuración de Streamlit Secrets
- Setup de CI/CD (opcional)

#### 5. **Alertas y Notificaciones**
**Prioridad:** Baja
**Complejidad:** Alta
**Descripción:** Sistema de alertas cuando:
- Hay datos nuevos disponibles en datos.gob.ar
- Se detectan anomalías en los datos (caídas abruptas)
- Los CSV están desactualizados (>1 mes)

**Tecnologías sugeridas:**
- Airflow para scheduling
- Email/Telegram para notificaciones
- Script de scraping de datos.gob.ar

#### 6. **Análisis Predictivo**
**Prioridad:** Media
**Complejidad:** Alta
**Descripción:** Agregar forecasting con Prophet o ARIMA para:
- Predecir inscripciones próximos 6 meses
- Identificar tendencias estacionales
- Detectar outliers

**Librerías sugeridas:**
- Prophet (Facebook)
- Statsmodels (ARIMA)
- Plotly para visualizar predicciones

#### 7. **Dashboard de Administración**
**Prioridad:** Baja
**Complejidad:** Media
**Descripción:** Panel administrativo para:
- Ver logs de carga de datos
- Reprocesar archivos
- Ver estado de tablas PostgreSQL
- Gestionar usuarios (si se comparte)

### Largo Plazo (3-6 meses):

#### 8. **API REST**
**Prioridad:** Baja
**Complejidad:** Alta
**Descripción:** Exponer datos via API REST con FastAPI para:
- Integración con otros sistemas
- Consultas programáticas
- Webhooks para actualizaciones

**Endpoints sugeridos:**
```
GET /api/v1/inscripciones?anio=2024&provincia=Buenos%20Aires
GET /api/v1/transferencias/ranking
GET /api/v1/totales/nacional?desde=2020&hasta=2025
```

#### 9. **Análisis de Maquinarias Agrícolas**
**Prioridad:** Media (si el usuario está en sector agro)
**Complejidad:** Media
**Descripción:** Pestaña dedicada solo a Maquinarias con:
- Análisis por tipo de maquinaria
- Correlación con cosechas
- Provincias agrícolas principales
- Estacionalidad de compra

**Fuentes de datos adicionales:**
- Ministerio de Agricultura (cosechas)
- INDEC (PBI agropecuario)
- Clima y precipitaciones

#### 10. **Machine Learning: Clustering de Provincias**
**Prioridad:** Baja
**Complejidad:** Alta
**Descripción:** Agrupar provincias con comportamiento similar en:
- Patrones de compra
- Estacionalidad
- Tipo de vehículos preferidos

**Algoritmos sugeridos:**
- K-means
- DBSCAN
- Hierarchical clustering

---

## 🔧 TROUBLESHOOTING

### Problema 1: No se ven los datos en la pestaña

**Síntomas:**
- La pestaña "Tendencias Históricas" aparece
- Muestra mensaje "⚠️ No hay datos de estadísticas agregadas cargados"

**Solución:**
```powershell
# Verificar que las tablas existan
psql -h localhost -U postgres -d mercado_automotor -c "SELECT COUNT(*) FROM estadisticas_inscripciones;"

# Si da error "relation does not exist", crear tablas:
psql -h localhost -U postgres -d mercado_automotor -f sql/crear_tablas_estadisticas_agregadas.sql

# Cargar datos:
python cargar_estadisticas_agregadas.py
```

### Problema 2: Error "No such file or directory: cargar_estadisticas_agregadas.py"

**Síntomas:**
- Al ejecutar `python cargar_estadisticas_agregadas.py`
- Error: FileNotFoundError

**Solución:**
```powershell
# Verificar que estés en el directorio correcto
pwd
# Debe mostrar: .../mercado_automotor

# Verificar que el archivo exista
dir cargar_estadisticas_agregadas.py

# Si no existe, hacer pull:
git pull origin claude/continue-project-011CUzjS5wAvCY8xCtvfzV16
```

### Problema 3: Gráficos no cargan / spinning infinito

**Síntomas:**
- La pestaña carga
- Los filtros aparecen
- Los gráficos muestran spinner (loading) infinitamente

**Solución:**
```powershell
# 1. Verificar que PostgreSQL esté corriendo
# Docker:
docker ps | grep postgres

# 2. Verificar conexión desde Python
python -c "from backend.config.settings import settings; from sqlalchemy import create_engine; engine = create_engine(settings.get_database_url_sync()); print('OK')"

# 3. Reiniciar Streamlit
# Ctrl+C en terminal
streamlit run frontend/app_datos_gob.py
```

### Problema 4: ngrok muestra "Visit Site" cada vez

**Síntomas:**
- Al compartir URL de ngrok
- Usuario ve pantalla "You are about to visit..."
- Debe hacer clic en "Visit Site"

**Causa:** Comportamiento normal de ngrok free tier

**Solución:**
```
Opción A (GRATIS): No hay solución, es limitación del free tier
Opción B (PAGO): ngrok Pro ($8/mes) elimina esta pantalla
Opción C (ALTERNATIVA): Usar Cloudflare Tunnel (gratis, más complejo)
```

### Problema 5: Datos desactualizados después de actualizar CSV

**Síntomas:**
- Descargaste nuevos CSV de datos.gob.ar
- Los colocaste en `data/estadisticas_dnrpa/`
- Ejecutaste `python cargar_estadisticas_agregadas.py`
- El dashboard sigue mostrando datos viejos

**Solución:**
```powershell
# 1. Verificar que se cargaron los datos
python cargar_estadisticas_agregadas.py
# Ver output: "Procesados: XXXX registros"

# 2. Verificar en PostgreSQL
psql -h localhost -U postgres -d mercado_automotor -c "SELECT MAX(anio), MAX(mes) FROM estadisticas_inscripciones WHERE tipo_vehiculo = 'Motovehículos';"

# 3. Limpiar caché de Streamlit
# Opción A: Presionar 'C' en el dashboard y luego "Clear cache"
# Opción B: Reiniciar Streamlit (Ctrl+C, luego streamlit run...)

# 4. Refrescar navegador (F5)
```

### Problema 6: Error al cambiar de branch

**Síntomas:**
```
error: The following untracked working tree files would be overwritten by checkout
```

**Solución:**
```powershell
# Hacer backup de archivos no trackeados
move cargar_estadisticas_agregadas.py cargar_estadisticas_agregadas.py.backup

# Cambiar de branch
git checkout claude/continue-project-011CUzjS5wAvCY8xCtvfzV16

# Restaurar backup si es necesario
move cargar_estadisticas_agregadas.py.backup cargar_estadisticas_agregadas.py
```

### Problema 7: Consultas muy lentas en el dashboard

**Síntomas:**
- Al cambiar filtros, tarda >10 segundos en actualizar
- Gráficos tardan en renderizar

**Solución:**
```sql
-- Verificar que los índices existan
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('estadisticas_inscripciones', 'estadisticas_transferencias');

-- Si no existen, crearlos:
CREATE INDEX idx_est_inscripciones_anio_mes ON estadisticas_inscripciones(anio, mes);
CREATE INDEX idx_est_inscripciones_provincia ON estadisticas_inscripciones(provincia);
CREATE INDEX idx_est_inscripciones_tipo ON estadisticas_inscripciones(tipo_vehiculo);

-- Actualizar estadísticas de PostgreSQL
ANALYZE estadisticas_inscripciones;
ANALYZE estadisticas_transferencias;
```

---

## 💻 COMANDOS ÚTILES

### Git:

```powershell
# Ver branch actual
git branch

# Cambiar a branch principal del proyecto
git checkout claude/continue-project-011CUzjS5wAvCY8xCtvfzV16

# Ver estado de archivos
git status

# Ver últimos 5 commits
git log --oneline -5

# Traer últimos cambios
git pull origin claude/continue-project-011CUzjS5wAvCY8xCtvfzV16

# Ver diferencias con remoto
git fetch origin
git diff claude/continue-project-011CUzjS5wAvCY8xCtvfzV16 origin/claude/continue-project-011CUzjS5wAvCY8xCtvfzV16
```

### PostgreSQL:

```powershell
# Conectar a base de datos
psql -h localhost -U postgres -d mercado_automotor

# Ver tamaño de base de datos
SELECT pg_size_pretty(pg_database_size('mercado_automotor'));

# Ver tamaño de tablas
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Contar registros
SELECT COUNT(*) FROM estadisticas_inscripciones;
SELECT COUNT(*) FROM estadisticas_transferencias;

# Ver últimos registros cargados
SELECT * FROM estadisticas_inscripciones
ORDER BY fecha_carga DESC
LIMIT 10;

# Backup de tablas
pg_dump -h localhost -U postgres -d mercado_automotor \
  -t estadisticas_inscripciones \
  -t estadisticas_transferencias \
  > backup_estadisticas.sql

# Restaurar backup
psql -h localhost -U postgres -d mercado_automotor < backup_estadisticas.sql
```

### Streamlit:

```powershell
# Iniciar dashboard
streamlit run frontend/app_datos_gob.py

# Iniciar en puerto específico
streamlit run frontend/app_datos_gob.py --server.port 8502

# Ver logs en tiempo real
streamlit run frontend/app_datos_gob.py --logger.level=debug

# Limpiar caché y reiniciar
streamlit cache clear
streamlit run frontend/app_datos_gob.py
```

### Python:

```powershell
# Verificar instalación de librerías
pip list | grep -E "streamlit|plotly|pandas|sqlalchemy"

# Instalar librerías faltantes
pip install streamlit plotly pandas sqlalchemy psycopg2-binary

# Verificar conexión a PostgreSQL
python -c "from backend.config.settings import settings; from sqlalchemy import create_engine; engine = create_engine(settings.get_database_url_sync()); print('Conexión OK')"

# Ver versión de Python
python --version

# Ejecutar script de carga con logs
python cargar_estadisticas_agregadas.py > carga_$(date +%Y%m%d).log 2>&1
```

### ngrok:

```powershell
# Iniciar túnel
ngrok http 8501

# Ver todas las conexiones activas
ngrok http 8501 --log=stdout

# Usar un dominio fijo (requiere cuenta paga)
ngrok http 8501 --domain=tu-dominio.ngrok.app
```

---

## 📝 NOTAS FINALES

### Lecciones Aprendidas:

1. **Branches múltiples:** El trabajo inició en `desarrollo/dashboard-datos-gob-2025` pero se finalizó en `claude/continue-project-011CUzjS5wAvCY8xCtvfzV16`. En futuras sesiones, confirmar branch objetivo desde el inicio.

2. **Push con error 403:** El entorno de Claude tiene restricciones de push. Los commits se hicieron exitosamente pero el push requirió intervención del usuario.

3. **Nombres dinámicos de archivos:** El script de carga usa glob patterns y selección por fecha de modificación, lo que lo hace robusto ante cambios mensuales de nombres.

4. **Datos agregados vs detallados:** Mantener ambos tipos de datos es útil:
   - Detallados: Para análisis profundos y granulares
   - Agregados: Para tendencias históricas y performance

### Decisiones de Diseño:

- **Por qué no usar API de datos.gob.ar:** Los datos agregados vienen en CSV. Automatizar la descarga sería complejo y frágil ante cambios en el sitio.

- **Por qué tablas separadas:** En lugar de agregar columnas a las tablas existentes, se crearon tablas nuevas para:
  - Mantener separación de conceptos
  - Evitar queries lentos en tablas grandes
  - Facilitar actualización independiente

- **Por qué Plotly:** Ya se usaba en el resto del dashboard. Mantener consistencia.

### Estado del Proyecto:

✅ **COMPLETADO Y FUNCIONAL**

- Todas las funcionalidades implementadas
- Datos cargados correctamente
- Dashboard funcionando en local
- Compartible vía ngrok
- Documentado exhaustivamente

### Contacto y Soporte:

Para dudas o problemas:
1. Revisar sección [Troubleshooting](#troubleshooting)
2. Verificar [Comandos Útiles](#comandos-útiles)
3. Revisar commits en GitHub para ver cambios exactos

---

**Documento generado:** 11 de Noviembre de 2025
**Última actualización:** 11 de Noviembre de 2025
**Versión:** 1.0
**Branch:** claude/continue-project-011CUzjS5wAvCY8xCtvfzV16
**Commit:** aae6df5

---

## 🎯 CHECKLIST PARA PRÓXIMA SESIÓN

Antes de comenzar una nueva sesión de desarrollo, verificar:

- [ ] Branch correcta: `claude/continue-project-011CUzjS5wAvCY8xCtvfzV16`
- [ ] PostgreSQL corriendo (`docker ps` o verificar servicio)
- [ ] Datos cargados en `estadisticas_inscripciones` y `estadisticas_transferencias`
- [ ] Dashboard funciona: `streamlit run frontend/app_datos_gob.py`
- [ ] Pestaña "Tendencias Históricas" visible y operativa
- [ ] Git status limpio (sin cambios pendientes)
- [ ] Backups recientes de PostgreSQL (opcional pero recomendado)

**¡Todo listo para continuar el desarrollo!** 🚀
