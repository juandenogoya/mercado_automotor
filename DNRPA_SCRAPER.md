# Scraper DNRPA - Datos Oficiales de Patentamientos

## Descripción

El scraper de DNRPA (Dirección Nacional del Registro de la Propiedad Automotor) obtiene datos **oficiales** de inscripciones (patentamientos) de vehículos en Argentina con granularidad provincial y por registro seccional.

### ¿Por qué DNRPA?

- ✅ **Fuente oficial del gobierno argentino**
- ✅ **Datos más completos y confiables** que cámaras automotrices
- ✅ **Granularidad provincial** - permite análisis geográfico
- ✅ **Granularidad por registro seccional** - nivel localidad
- ✅ **Separación por tipo de vehículo** (Autos, Motos, Maquinarias)
- ✅ **Datos mensuales históricos**

## Fuente de Datos

**URL Base**: https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/

### Estructura de Consultas

1. **Selección inicial**:
   - Año (lista desplegable)
   - Tipo de vehículo: Autos (A), Motos (M), Maquinarias (Q)

2. **Primera tabla** (`tram_prov.php`):
   - Filas: Provincias (24 provincias argentinas)
   - Columnas: Meses (Enero a Diciembre)
   - Valores: Cantidad de inscripciones

3. **Segunda tabla** (`tram_prov_XX.php`):
   - Filas: Registros Seccionales (por localidad)
   - Columnas: Meses
   - Valores: Cantidad de inscripciones

### Provincias Soportadas

Código | Provincia
-------|----------
01 | Capital Federal
02 | Buenos Aires
03 | Catamarca
04 | Córdoba
05 | Corrientes
06 | Chaco
07 | Chubut
08 | Entre Ríos
09 | Formosa
10 | Jujuy
11 | La Pampa
12 | La Rioja
13 | Mendoza
14 | Misiones
15 | Neuquén
16 | Río Negro
17 | Salta
18 | San Juan
19 | San Luis
20 | Santa Cruz
21 | Santa Fe
22 | Santiago del Estero
23 | Tucumán
24 | Tierra del Fuego

## Uso del Scraper

### Importar el scraper

```python
from backend.scrapers import DNRPAScraper
```

### Ejemplo 1: Resumen provincial

```python
scraper = DNRPAScraper()

# Obtener resumen de todas las provincias para 2024, Autos
df_resumen = scraper.get_provincias_summary(
    anio=2024,
    codigo_tipo='A'  # Autos
)

print(df_resumen)
# Columnas: Provincia, Enero, Febrero, ..., Diciembre, Total
```

### Ejemplo 2: Detalle de una provincia

```python
# Obtener detalle de Buenos Aires (código 02) para 2024
df_detalle = scraper.get_provincia_detalle(
    codigo_provincia='02',  # Buenos Aires
    anio=2024,
    codigo_tipo='A'  # Autos
)

print(df_detalle)
# Columnas: Registro_Seccional, Enero, ..., Diciembre, Total, provincia_codigo, provincia_nombre
```

### Ejemplo 3: Scrape completo con guardado en BD

```python
from backend.scrapers.dnrpa_scraper import scrape_dnrpa

# Scrape año 2024, Autos, y guardar en base de datos
resultado = scrape_dnrpa(
    anio=2024,
    tipo_vehiculo='A',
    guardar_bd=True
)

print(resultado)
# {
#     'status': 'success',
#     'anio': 2024,
#     'total_guardados_bd': 2880,  # (24 provincias × 12 meses + detalles)
#     'provincias': 24,
#     'errores': []
# }
```

### Ejemplo 4: Scrape múltiples tipos de vehículos

```python
scraper = DNRPAScraper()

for tipo_codigo, tipo_nombre in scraper.TIPOS_VEHICULO.items():
    print(f"\nScraping {tipo_nombre}...")

    resultado = scraper.scrape_all_provincias(
        anio=2024,
        codigo_tipo=tipo_codigo,
        incluir_detalle=True
    )

    # Guardar en BD
    for codigo_prov, df in resultado['detalles'].items():
        scraper.save_to_database(df, tipo_vehiculo='0km')
```

## Integración con Airflow

El scraper está integrado en el DAG mensual:

```python
# airflow/dags/mercado_automotor_etl.py

task_dnrpa = PythonOperator(
    task_id='scrape_dnrpa_patentamientos',
    python_callable=scrape_dnrpa,
)

# Se ejecuta el día 5 de cada mes a las 8 AM
# junto con ACARA y ADEFA
```

### Programación

- **Frecuencia**: Mensual
- **Día**: 5 de cada mes
- **Hora**: 8:00 AM
- **Ejecución paralela con**: ACARA, ADEFA

## Datos Almacenados

### Tabla: `patentamientos`

Campo | Tipo | Descripción
------|------|------------
fecha | Date | Fecha del registro (primer día del mes)
anio | Integer | Año
mes | Integer | Mes (1-12)
tipo_vehiculo | String | '0km' o 'usado'
marca | String | 'TOTAL' (DNRPA no desglosa por marca)
cantidad | Integer | Cantidad de inscripciones
**provincia** | String | **NUEVO**: Nombre de provincia o registro seccional
fuente | String | 'DNRPA'
periodo_reportado | String | 'YYYY-MM'

### Consultas Útiles

```sql
-- Patentamientos por provincia en 2024
SELECT
    provincia,
    SUM(cantidad) as total_patentamientos
FROM patentamientos
WHERE
    fuente = 'DNRPA'
    AND anio = 2024
    AND tipo_vehiculo = '0km'
GROUP BY provincia
ORDER BY total_patentamientos DESC;

-- Top 5 provincias con mayor crecimiento YoY
WITH comparacion AS (
    SELECT
        provincia,
        SUM(CASE WHEN anio = 2024 THEN cantidad ELSE 0 END) as total_2024,
        SUM(CASE WHEN anio = 2023 THEN cantidad ELSE 0 END) as total_2023
    FROM patentamientos
    WHERE fuente = 'DNRPA' AND provincia IS NOT NULL
    GROUP BY provincia
)
SELECT
    provincia,
    total_2024,
    total_2023,
    ROUND(((total_2024 - total_2023)::FLOAT / NULLIF(total_2023, 0)) * 100, 2) as crecimiento_pct
FROM comparacion
WHERE total_2023 > 0
ORDER BY crecimiento_pct DESC
LIMIT 5;
```

## Ventajas vs ACARA/FACCARA

Característica | DNRPA | ACARA/FACCARA
--------------|-------|---------------
Oficialidad | ✅ Gobierno | ⚠️ Cámara privada
Granularidad geográfica | ✅ Provincial + Local | ❌ Solo nacional
Confiabilidad | ✅ Alta | ⚠️ Media
Detalle por marca | ❌ No | ✅ Sí
Tipos de vehículo | ✅ Autos, Motos, Maquinarias | ✅ 0km, Usados
Actualización | 🔄 Mensual | 🔄 Mensual
Accesibilidad | ✅ Público | ✅ Público

## Recomendación de Uso

**Estrategia Dual**:

1. **DNRPA** para:
   - Totales oficiales confiables
   - Análisis geográfico (por provincia/localidad)
   - Validación de otras fuentes
   - Datos de motos y maquinarias

2. **ACARA/FACCARA** para:
   - Detalle por marca y modelo
   - Análisis competitivo
   - Segmentación de mercado

3. **Cruzar ambas fuentes** para:
   - Validar totales
   - Detectar inconsistencias
   - Análisis más robusto

## Limitaciones

- ⚠️ No desglosa por marca (solo totales)
- ⚠️ No separa 0km vs usados explícitamente
- ⚠️ Puede tener demoras en actualización de datos recientes
- ⚠️ Scraping puede ser lento (24 provincias × 12 meses)
- ⚠️ Rate limiting: 2 segundos entre requests

## Configuración

### Variables de Entorno

```env
SCRAPING_USER_AGENT="Mozilla/5.0..."  # User agent para requests
SCRAPING_TIMEOUT=30  # Timeout en segundos
```

### Delay entre Requests

```python
# En DNRPAScraper
self.delay_between_requests = 2  # segundos
```

**Ajustar según necesidad**:
- Desarrollo/testing: 1 segundo
- Producción: 2-3 segundos (respetar el servidor)

## Migración de Base de Datos

Para agregar el campo `provincia` a la tabla existente:

```bash
# Aplicar migración SQL
psql -U mercado_automotor -d mercado_automotor_db -f migrations/001_add_provincia_to_patentamientos.sql
```

O usando Docker:

```bash
docker-compose exec db psql -U mercado_automotor -d mercado_automotor_db -f /migrations/001_add_provincia_to_patentamientos.sql
```

## Testing

### Test manual del scraper

```bash
# Ejecutar el scraper standalone
python -m backend.scrapers.dnrpa_scraper
```

### Test con pytest

```python
# tests/test_dnrpa_scraper.py
import pytest
from backend.scrapers import DNRPAScraper

def test_dnrpa_provincias_summary():
    scraper = DNRPAScraper()
    df = scraper.get_provincias_summary(anio=2024, codigo_tipo='A')

    assert df is not None
    assert len(df) == 24  # 24 provincias
    assert 'Enero' in df.columns
    assert 'Diciembre' in df.columns
```

## Mantenimiento

### Verificación de Códigos

Los códigos de provincia y tipo de vehículo están hardcodeados en `DNRPAScraper.PROVINCIAS` y `DNRPAScraper.TIPOS_VEHICULO`.

Si cambian en el sitio web de DNRPA:
1. Actualizar diccionarios en `backend/scrapers/dnrpa_scraper.py`
2. Ejecutar tests
3. Crear nueva versión

### Monitoreo de Errores

El scraper registra errores detallados con loguru:

```python
logger.error(f"[DNRPA] Error obteniendo provincia {codigo_prov}: {e}")
```

Revisar logs en:
- Desarrollo: `logs/app.log`
- Producción: Airflow task logs

## Contacto y Soporte

- **Fuente oficial**: https://www.dnrpa.gov.ar/
- **Consultas técnicas**: Revisar documentación del scraper
- **Issues**: Reportar en el repositorio del proyecto

---

**Fecha de última actualización**: 2025-11-08
**Versión del scraper**: 1.0.0
**Status**: ✅ Producción
