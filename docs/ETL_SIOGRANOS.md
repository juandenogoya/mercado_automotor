# ETL SIOGRANOS - Documentación

## 📋 Descripción

Sistema ETL (Extract, Transform, Load) para cargar datos históricos de operaciones de granos desde la API SIOGRANOS al PostgreSQL del proyecto.

**Objetivo**: Tener datos completos desde 2020-01-01 hasta la fecha para correlacionar con el mercado automotor.

## 🎯 ¿Por qué SIOGRANOS?

La actividad agrícola (especialmente soja, maíz, trigo) tiene **correlación directa** con la venta de:
- **Pick-ups** (Toyota Hilux, Ford Ranger, VW Amarok)
- **Camiones** de transporte de granos
- **Vehículos comerciales** en zonas rurales

**Hipótesis**: Precio soja ↑ → Liquidez rural ↑ → Ventas pick-ups ↑ (delay 3-6 meses)

---

## 🏗️ Arquitectura

### Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                     API SIOGRANOS                               │
│  https://test.bc.org.ar/SiogranosAPI/api/ConsultaPublica/...   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ HTTP GET (con reintentos)
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                  etl_siogranos.py                               │
│  • Divide período en chunks de 7 días                          │
│  • Reintentos exponenciales (2s, 4s, 8s, 16s)                  │
│  • Transforma JSON → PostgreSQL                                 │
│  • Maneja duplicados (ON CONFLICT)                              │
│  • Logging completo                                             │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ INSERT bulk (1000 rows/batch)
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│               PostgreSQL - Base de Datos                        │
│  • Tabla: siogranos_operaciones                                 │
│  • Tabla control: siogranos_etl_control                         │
│  • Índices optimizados (fecha, grano, provincia)                │
│  • Vistas analíticas                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Estrategia de Chunking

**Problema**: 58k operaciones en 30 días → Consultas largas causan timeout

**Solución**: Dividir en chunks de **7 días** (1 semana)

```
2020-01-01 → 2025-11-10 = ~2,070 días
2,070 días ÷ 7 días/chunk = ~296 chunks
```

### Manejo de Errores

```python
# Reintentos exponenciales
Intento 1: Falla → Espera 2s
Intento 2: Falla → Espera 4s
Intento 3: Falla → Espera 8s
Intento 4: Falla → Espera 16s
Intento 5: Registra error y continúa con siguiente chunk
```

### Deduplicación

```sql
-- Constraint en la tabla
CONSTRAINT unique_operacion_fecha UNIQUE (id_operacion, fecha_operacion)

-- Insert con ON CONFLICT
INSERT INTO siogranos_operaciones (...)
VALUES (...)
ON CONFLICT (id_operacion, fecha_operacion)
DO UPDATE SET fecha_actualizacion = CURRENT_TIMESTAMP
```

---

## 🚀 Instalación y Setup

### 1. Prerequisitos

```bash
# Python 3.8+
python --version

# PostgreSQL 12+
psql --version
```

### 2. Instalar dependencias

```bash
pip install requests psycopg2-binary python-dotenv tabulate
```

### 3. Configurar base de datos

```bash
# Crear base de datos (si no existe)
createdb mercado_automotor

# Crear schema
psql -d mercado_automotor -f database/schemas/siogranos_schema.sql
```

Esto crea:
- ✅ Tabla `siogranos_operaciones` (datos de operaciones)
- ✅ Tabla `siogranos_etl_control` (control de chunks procesados)
- ✅ Índices optimizados
- ✅ Vistas analíticas

### 4. Configurar variables de entorno

```bash
# Crear archivo .env en la raíz del proyecto
cat > .env << EOF
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mercado_automotor
DB_USER=postgres
DB_PASSWORD=tu_password

# API SIOGRANOS
SIOGRANOS_API_URL=https://test.bc.org.ar/SiogranosAPI/api/ConsultaPublica/consultarOperaciones
EOF
```

**⚠️ IMPORTANTE**: Si tienes URL de **producción** (no testing), úsala aquí.

---

## 📦 Uso

### Carga inicial (histórico completo)

```bash
# Carga desde 2020-01-01 hasta hoy
python etl_siogranos.py
```

**Salida esperada**:
```
================================================================================
🌾 ETL SIOGRANOS - Carga Histórica
================================================================================
📅 Período: 2020-01-01 → 2025-11-10
📦 Tamaño chunk: 7 días
🔄 Reintentos máximos: 4
🔗 API: https://test.bc.org.ar/...
================================================================================

✅ Conexión a PostgreSQL establecida
📋 Total de chunks a procesar: 296

================================================================================
📦 PROCESANDO CHUNK: 2020-01-01 → 2020-01-07
================================================================================
📡 Consultando API: 2020-01-01 a 2020-01-07 (intento 1/4)
✅ Respuesta exitosa: 2,847 operaciones
🔄 Transformando 2,847 operaciones...
✅ Transformadas: 2,847 operaciones
💾 Insertando en PostgreSQL...
✅ Insertados: 2,847 | Duplicados: 0 | Errores: 0
⏱️ Duración: 3.2s

🔄 Progreso: 1/296 (0%)

[... continúa procesando ...]

================================================================================
📊 RESUMEN FINAL
================================================================================
✅ Chunks procesados: 296/296
📊 Registros procesados: 845,923
💾 Registros insertados: 845,923
🔄 Registros duplicados: 0
❌ Registros con error: 0
================================================================================

✅ ETL completado exitosamente
```

### Verificar progreso

```bash
# Ver estado de chunks
python verificar_chunks_siogranos.py
```

**Salida**:
```
================================================================================
🔍 VERIFICACIÓN DE CHUNKS - SIOGRANOS ETL
================================================================================
✅ Conectado a PostgreSQL

📊 RESUMEN GENERAL
--------------------------------------------------------------------------------
Total de chunks: 296
✅ Completados: 150 (51%)
⏳ Pendientes: 146 (49%)
❌ Con errores: 0

📈 ESTADÍSTICAS DE DATOS CARGADOS
--------------------------------------------------------------------------------
Total registros: 422,961
Días con datos: 1,050
Fecha mínima: 2020-01-01
Fecha máxima: 2022-11-15
Granos diferentes: 8
Provincias: 15
Volumen total: 12,847,293.50 TN
Precio promedio: $24,532.75/TN

[... más estadísticas ...]
```

### Reanudar carga interrumpida

Si el ETL se interrumpe (Ctrl+C, error de red, etc.), simplemente **vuélvelo a ejecutar**:

```bash
python etl_siogranos.py
```

El script automáticamente:
- ✅ Detecta chunks ya completados (los omite)
- ✅ Retoma desde el último chunk pendiente
- ✅ No duplica datos

### Actualización incremental (uso diario)

Para mantener datos actualizados, programa ejecución semanal:

```bash
# Crontab: Cada lunes a las 2am
0 2 * * 1 cd /ruta/proyecto && python etl_siogranos.py >> logs/etl_siogranos.log 2>&1
```

---

## 📊 Estructura de Datos

### Tabla: `siogranos_operaciones`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BIGSERIAL | ID interno (auto-increment) |
| `id_operacion` | VARCHAR | ID de operación en SIOGRANOS |
| `fecha_operacion` | DATE | Fecha de la operación |
| `id_grano` | INTEGER | Código del grano (21=Soja, 2=Maíz, 1=Trigo) |
| `nombre_grano` | VARCHAR | Nombre del grano |
| `volumen_tn` | DECIMAL | Volumen en toneladas |
| `precio_tn` | DECIMAL | Precio por tonelada |
| `monto_total` | DECIMAL | Volumen × Precio |
| `simbolo_moneda` | VARCHAR | $ (pesos), USD, EUR |
| `id_provincia_procedencia` | VARCHAR | Código provincia (B=Buenos Aires, S=Santa Fe, etc.) |
| `nombre_provincia_procedencia` | VARCHAR | Nombre provincia |
| `id_localidad_procedencia` | VARCHAR | Código localidad |
| `nombre_localidad_procedencia` | VARCHAR | Nombre localidad |
| ... | ... | (30+ campos adicionales) |

### Índices principales

```sql
-- Consultas por fecha (más común)
idx_siogranos_fecha_operacion

-- Filtros por grano
idx_siogranos_id_grano

-- Análisis geográfico
idx_siogranos_provincia_procedencia

-- Consulta compuesta típica
idx_siogranos_grano_prov_fecha (id_grano, id_provincia_procedencia, fecha_operacion)
```

---

## 📈 Vistas Analíticas

### 1. Resumen por Provincia y Mes

```sql
SELECT * FROM v_siogranos_resumen_provincial
WHERE provincia = 'BUENOS AIRES'
  AND mes >= '2024-01-01'
ORDER BY mes DESC;
```

**Campos**:
- `mes`: Mes (truncado)
- `provincia`: Provincia
- `total_operaciones`: Cantidad de operaciones
- `volumen_total_tn`: Volumen total en toneladas
- `precio_promedio_tn`: Precio promedio ponderado
- `monto_total`: Valor total de operaciones
- `tipos_granos`: Cantidad de granos diferentes

### 2. Índice de Liquidez Agropecuaria

```sql
SELECT * FROM v_siogranos_indice_liquidez
WHERE mes >= '2023-01-01'
ORDER BY liquidez_millones DESC
LIMIT 20;
```

**Uso**: Identificar provincias con mayor liquidez rural (potencial de ventas automotor)

### 3. Top Productos por Provincia

```sql
SELECT * FROM v_siogranos_top_productos_provincia
WHERE provincia = 'CORDOBA'
  AND ranking <= 3;
```

---

## 🔍 Consultas Útiles

### Precio promedio de soja por mes (últimos 24 meses)

```sql
SELECT
    DATE_TRUNC('month', fecha_operacion) AS mes,
    AVG(precio_tn) AS precio_promedio_soja,
    SUM(volumen_tn) AS volumen_total_tn,
    COUNT(*) AS operaciones
FROM siogranos_operaciones
WHERE nombre_grano = 'SOJA'
  AND fecha_operacion >= CURRENT_DATE - INTERVAL '24 months'
  AND simbolo_moneda = 'USD'
GROUP BY DATE_TRUNC('month', fecha_operacion)
ORDER BY mes DESC;
```

### Provincias con mayor actividad (últimos 12 meses)

```sql
SELECT
    nombre_provincia_procedencia AS provincia,
    COUNT(*) AS total_operaciones,
    SUM(volumen_tn) AS volumen_total_tn,
    SUM(monto_total) / 1000000.0 AS monto_millones
FROM siogranos_operaciones
WHERE fecha_operacion >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY nombre_provincia_procedencia
ORDER BY volumen_total_tn DESC
LIMIT 10;
```

### Correlación temporal: Precio soja vs Mes

```sql
-- Exportar para cruzar con ventas automotor
SELECT
    DATE_TRUNC('month', fecha_operacion) AS mes,
    AVG(precio_tn) AS precio_soja_usd,
    SUM(volumen_tn) AS volumen_soja_tn
FROM siogranos_operaciones
WHERE nombre_grano = 'SOJA'
  AND simbolo_moneda = 'USD'
  AND fecha_operacion BETWEEN '2020-01-01' AND '2024-12-31'
GROUP BY DATE_TRUNC('month', fecha_operacion)
ORDER BY mes;
```

---

## 🛠️ Troubleshooting

### Error: "Connection refused to PostgreSQL"

```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Iniciar si está detenido
sudo systemctl start postgresql

# Verificar conexión
psql -h localhost -U postgres -d mercado_automotor
```

### Error: "API timeout" frecuente

**Causa**: Servidor lento o red inestable

**Solución**: Ajustar parámetros en `etl_siogranos.py`

```python
# Aumentar timeout
REQUEST_TIMEOUT = 120  # De 60s a 120s

# Reducir tamaño de chunk
CHUNK_DAYS = 3  # De 7 a 3 días
```

### Muchos duplicados al re-ejecutar

**Es normal**. La tabla tiene constraint `UNIQUE (id_operacion, fecha_operacion)`:
- ✅ Registros duplicados → Se cuentan pero **no se insertan**
- ✅ No afecta integridad de datos

### Servidor de testing sin datos

Si usas `https://test.bc.org.ar/...` y obtienes 0 operaciones:

**Solución**: Obtener URL de **producción**

```bash
# Contactar a SIOGRANOS o Bolsa de Comercio
# Actualizar .env con URL de producción
SIOGRANOS_API_URL=https://api.bc.org.ar/SiogranosAPI/...  # URL real
```

---

## ⚙️ Configuración Avanzada

### Modificar período de carga

Editar `etl_siogranos.py`:

```python
# Cambiar fecha de inicio
FECHA_INICIO = datetime(2022, 1, 1)  # En lugar de 2020

# O usar rango específico
FECHA_INICIO = datetime(2023, 6, 1)
FECHA_FIN = datetime(2023, 12, 31)
```

### Agregar campos personalizados

Si la API devuelve campos adicionales, agregar a `transformar_operacion()`:

```python
def transformar_operacion(operacion: Dict) -> Dict:
    transformado = {
        # ... campos existentes ...

        # Nuevo campo
        'campo_nuevo': operacion.get('campoNuevo'),
    }
    return transformado
```

Y actualizar schema SQL:

```sql
ALTER TABLE siogranos_operaciones
ADD COLUMN campo_nuevo VARCHAR(100);
```

---

## 📝 Logs

El ETL genera dos tipos de logs:

### 1. Archivo: `etl_siogranos.log`

```bash
# Ver últimas líneas
tail -f etl_siogranos.log

# Buscar errores
grep "ERROR" etl_siogranos.log

# Estadísticas de un día específico
grep "2024-03-15" etl_siogranos.log
```

### 2. Tabla: `siogranos_etl_control`

```sql
-- Ver últimas ejecuciones
SELECT
    fecha_desde,
    fecha_hasta,
    estado,
    registros_insertados,
    registros_duplicados,
    duracion_segundos,
    fin_ejecucion
FROM siogranos_etl_control
ORDER BY fin_ejecucion DESC
LIMIT 20;

-- Chunks con errores
SELECT *
FROM siogranos_etl_control
WHERE estado = 'failed'
ORDER BY fecha_desde;
```

---

## 🎯 Próximos Pasos

Una vez cargados los datos:

### 1. Análisis Exploratorio

```bash
# Jupyter Notebook para explorar datos
jupyter notebook notebooks/analisis_siogranos.ipynb
```

### 2. Correlación con Datos Automotor

```sql
-- Crear tabla combinada para análisis
CREATE TABLE analisis_soja_pickups AS
SELECT
    s.mes,
    s.precio_promedio_soja,
    s.volumen_total_tn,
    a.ventas_pickups,
    a.ventas_camiones
FROM v_siogranos_resumen_granos s
LEFT JOIN ventas_automotor_mensuales a ON s.mes = a.mes
WHERE s.nombre_grano = 'SOJA'
ORDER BY s.mes;
```

### 3. Modelo Predictivo

```python
# Script: models/prediccion_pickups.py
# Variables entrada: precio_soja, volumen, provincia
# Variable salida: ventas_pickups (3 meses adelante)
```

---

## 📚 Referencias

- [API SIOGRANOS Docs](https://www.bolsadecereales.com/siogranos)
- [Códigos de Granos](./siogranos_codigos.py)
- [Schema PostgreSQL](./database/schemas/siogranos_schema.sql)

---

## 👤 Contacto

Para dudas o mejoras, contactar al equipo de desarrollo.

---

**Última actualización**: 2025-11-10
