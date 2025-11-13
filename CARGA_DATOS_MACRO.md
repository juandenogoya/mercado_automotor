# 📊 Carga de Datos Macroeconómicos

Guía completa para cargar datos macroeconómicos en PostgreSQL.

---

## 📋 Tablas Creadas

### 1. **IPC** (Índice de Precios al Consumidor)
- **Fuente**: INDEC API
- **Frecuencia**: Mensual
- **Delay**: ~15 días del mes siguiente
- **Columnas**:
  - `fecha`: Fecha del período (primer día del mes)
  - `nivel_general`: Índice base IPC
  - `variacion_mensual`: % mes vs mes anterior
  - `variacion_interanual`: % mes vs mismo mes año anterior
  - `variacion_acumulada`: % acumulada del año
  - `anio`, `mes`, `periodo_reportado`

### 2. **BADLAR** (Tasa de Interés)
- **Fuente**: BCRA API
- **Frecuencia**: Diaria (días hábiles)
- **Delay**: 2-3 días
- **Columnas**:
  - `fecha`: Fecha de la cotización
  - `tasa`: Tasa BADLAR (% TNA)
  - `unidad`: % TNA
  - `descripcion`: BADLAR bancos privados

### 3. **Tipo de Cambio**
- **Fuente**: BCRA API
- **Frecuencia**: Diaria (días hábiles)
- **Delay**: 2-3 días
- **Columnas**:
  - `fecha`: Fecha de la cotización
  - `tipo`: mayorista, minorista, etc.
  - `promedio`: Precio de referencia (USD/ARS)
  - `compra`, `venta`: Precios (si disponibles)
  - `moneda`: USD

---

## 🚀 Carga de Datos

### **Opción 1: Usando manage.py (Recomendado)**

#### Cargar todos los datos (últimos 5 años)
```bash
python manage.py cargar-macro
```

#### Cargar datos históricos completos (desde 2016)
```bash
python manage.py cargar-macro --historico
```

#### Cargar solo IPC
```bash
python manage.py cargar-macro --tipo ipc
```

#### Cargar solo BADLAR
```bash
python manage.py cargar-macro --tipo badlar
```

#### Cargar solo Tipo de Cambio
```bash
python manage.py cargar-macro --tipo tipo_cambio
# o abreviado:
python manage.py cargar-macro --tipo tc
```

#### Cargar histórico de BADLAR y Tipo de Cambio
```bash
python manage.py cargar-macro --tipo badlar --historico
python manage.py cargar-macro --tipo tc --historico
```

---

### **Opción 2: Usando el script directo**

El script `backend/scripts/cargar_datos_macro.py` ofrece más opciones avanzadas.

#### Cargar todos los datos
```bash
python backend/scripts/cargar_datos_macro.py --all
```

#### Cargar histórico completo
```bash
python backend/scripts/cargar_datos_macro.py --all --historico
```

#### Cargar rango personalizado
```bash
python backend/scripts/cargar_datos_macro.py --all --desde 2019-01-01 --hasta 2024-12-31
```

#### Cargar solo IPC
```bash
python backend/scripts/cargar_datos_macro.py --ipc
```

#### Cargar solo BADLAR
```bash
python backend/scripts/cargar_datos_macro.py --badlar
```

#### Cargar solo Tipo de Cambio
```bash
python backend/scripts/cargar_datos_macro.py --tipo-cambio
```

---

## 📊 Verificar Datos Cargados

### Ver estadísticas de todas las tablas
```bash
python manage.py stats
```

**Salida esperada:**
```
📊 Estadísticas de la base de datos:
  - Patentamientos: 0 registros
  - Producción: 0 registros
  - BCRA Indicadores: 0 registros
  - MercadoLibre Listings: 0 registros
  - IPC: 106 registros
  - BADLAR: 1,250 registros
  - Tipo de Cambio: 1,250 registros
```

### Consultar directamente desde PostgreSQL

```sql
-- Ver últimos registros de IPC
SELECT * FROM ipc ORDER BY fecha DESC LIMIT 10;

-- Ver últimos registros de BADLAR
SELECT * FROM badlar ORDER BY fecha DESC LIMIT 10;

-- Ver últimos registros de Tipo de Cambio
SELECT * FROM tipo_cambio ORDER BY fecha DESC LIMIT 10;

-- Contar registros por tabla
SELECT
    (SELECT COUNT(*) FROM ipc) as ipc,
    (SELECT COUNT(*) FROM badlar) as badlar,
    (SELECT COUNT(*) FROM tipo_cambio) as tipo_cambio;
```

---

## 🔄 Actualización Periódica

### Carga diaria (BADLAR y Tipo de Cambio)

```bash
# Cargar últimos 30 días
python backend/scripts/cargar_datos_macro.py --badlar --tipo-cambio --desde 2024-10-01
```

### Carga mensual (IPC)

```bash
# Cargar últimos 3 meses
python backend/scripts/cargar_datos_macro.py --ipc --desde 2024-08-01
```

---

## 🛠️ Uso desde Python

### Cliente INDEC (IPC)

```python
from datetime import date
from dateutil.relativedelta import relativedelta
from backend.api_clients.indec_client import INDECClient

client = INDECClient()

# Cargar últimos 2 años de IPC
fecha_hasta = date.today()
fecha_desde = fecha_hasta - relativedelta(years=2)

result = client.sync_ipc(fecha_desde, fecha_hasta)
print(f"Guardados: {result['records_saved']} registros")
```

### Cliente BCRA (BADLAR)

```python
from datetime import date
from dateutil.relativedelta import relativedelta
from backend.api_clients.bcra_client import BCRAClient

client = BCRAClient()

# Cargar últimos 6 meses de BADLAR
fecha_hasta = date.today()
fecha_desde = fecha_hasta - relativedelta(months=6)

result = client.sync_badlar(fecha_desde, fecha_hasta)
print(f"Guardados: {result['records_saved']} registros")
```

### Cliente BCRA (Tipo de Cambio)

```python
from datetime import date
from dateutil.relativedelta import relativedelta
from backend.api_clients.bcra_client import BCRAClient

client = BCRAClient()

# Cargar últimos 6 meses de Tipo de Cambio
fecha_hasta = date.today()
fecha_desde = fecha_hasta - relativedelta(months=6)

result = client.sync_tipo_cambio(fecha_desde, fecha_hasta)
print(f"Guardados: {result['records_saved']} registros")
```

---

## 🔍 Consultas Útiles

### IPC: Últimos 12 meses de inflación
```sql
SELECT
    fecha,
    anio,
    mes,
    variacion_mensual,
    variacion_interanual,
    variacion_acumulada
FROM ipc
ORDER BY fecha DESC
LIMIT 12;
```

### BADLAR: Promedio de tasa por mes
```sql
SELECT
    DATE_TRUNC('month', fecha) as mes,
    AVG(tasa) as tasa_promedio,
    MIN(tasa) as tasa_minima,
    MAX(tasa) as tasa_maxima
FROM badlar
WHERE fecha >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY mes
ORDER BY mes DESC;
```

### Tipo de Cambio: Evolución últimos 30 días
```sql
SELECT
    fecha,
    tipo,
    promedio,
    (promedio - LAG(promedio) OVER (ORDER BY fecha)) as variacion_diaria,
    ((promedio - LAG(promedio) OVER (ORDER BY fecha)) / LAG(promedio) OVER (ORDER BY fecha) * 100) as variacion_porcentual
FROM tipo_cambio
WHERE fecha >= CURRENT_DATE - INTERVAL '30 days'
  AND tipo = 'mayorista'
ORDER BY fecha DESC;
```

### Correlación IPC vs Tipo de Cambio (mensual)
```sql
WITH ipc_mensual AS (
    SELECT
        DATE_TRUNC('month', fecha) as mes,
        AVG(variacion_mensual) as ipc_var
    FROM ipc
    GROUP BY mes
),
tc_mensual AS (
    SELECT
        DATE_TRUNC('month', fecha) as mes,
        AVG(promedio) as tc_promedio
    FROM tipo_cambio
    WHERE tipo = 'mayorista'
    GROUP BY mes
)
SELECT
    i.mes,
    i.ipc_var,
    t.tc_promedio,
    (t.tc_promedio - LAG(t.tc_promedio) OVER (ORDER BY i.mes)) / LAG(t.tc_promedio) OVER (ORDER BY i.mes) * 100 as tc_var_mensual
FROM ipc_mensual i
JOIN tc_mensual t ON i.mes = t.mes
WHERE i.mes >= CURRENT_DATE - INTERVAL '12 months'
ORDER BY i.mes DESC;
```

---

## ⚠️ Troubleshooting

### Error: No se pueden crear las tablas

```bash
# Inicializar base de datos primero
python manage.py init-db
```

### Error: Conexión a PostgreSQL falla

Verificar variables de entorno en `.env`:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mercado_automotor
```

### Error: API INDEC timeout

La API de INDEC puede ser lenta. Aumentar timeout:
```python
# En backend/api_clients/indec_client.py
self.timeout = 60  # aumentar de 30 a 60 segundos
```

### Error: API BCRA devuelve 429 (Too Many Requests)

Esperar unos segundos y reintentar. El BCRA tiene rate limiting.

### Datos duplicados

Los scripts verifican duplicados automáticamente. Si hay valores diferentes, se actualizan.

---

## 📅 Plan de Carga Recomendado

### Carga Inicial (una vez)

```bash
# 1. Inicializar base de datos
python manage.py init-db

# 2. Cargar datos históricos completos
python manage.py cargar-macro --historico

# Esto cargará:
# - IPC: ~106 meses (desde 2016)
# - BADLAR: ~2,300 días hábiles (desde 2016)
# - Tipo de Cambio: ~2,300 días hábiles (desde 2016)
```

### Actualización Diaria (automatizar con cron/airflow)

```bash
# Actualizar BADLAR y Tipo de Cambio (diarios)
python manage.py cargar-macro --tipo badlar
python manage.py cargar-macro --tipo tc
```

### Actualización Mensual (día 20 de cada mes)

```bash
# Actualizar IPC (mensual)
python manage.py cargar-macro --tipo ipc
```

---

## 🎯 Próximos Pasos

1. ✅ **Verificar que los datos se cargaron correctamente**
   ```bash
   python manage.py stats
   ```

2. **Crear DAG de Airflow para actualización automática**
   - DAG diario para BADLAR y Tipo de Cambio
   - DAG mensual para IPC (día 20)

3. **Integrar con dashboard Streamlit**
   - Gráficos de IPC
   - Evolución de BADLAR
   - Tipo de cambio histórico

4. **Crear indicadores derivados**
   - Tasa real (BADLAR - Inflación)
   - Dólar ajustado por inflación
   - Accesibilidad de compra (TC × BADLAR × IPC)

---

## 📚 APIs Utilizadas

### INDEC API
- **URL**: https://apis.datos.gob.ar/series/api
- **Documentación**: https://datosgobar.github.io/series-tiempo-ar-api/
- **Series IPC**:
  - Nivel General: `148.3_INIVELNAL_DICI_M_26`
  - Variación Mensual: `148.3_INIVELNALNAL_DICI_M_32`
  - Variación Interanual: `148.3_INIVELNALNAL_DICI_M_31`

### BCRA API
- **URL**: https://api.bcra.gob.ar
- **Documentación**: https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp
- **Variables**:
  - BADLAR: ID 7
  - Tipo de Cambio BNA: ID 1
  - Reservas: ID 2
  - Créditos totales: ID 16

---

## ✨ Resumen

Has creado exitosamente:
- ✅ 3 tablas PostgreSQL para datos macroeconómicos
- ✅ 2 clientes API (INDEC y BCRA)
- ✅ Scripts de carga con validación de duplicados
- ✅ Comandos en manage.py para uso fácil
- ✅ Documentación completa

¡Todo listo para empezar a cargar datos! 🚀
