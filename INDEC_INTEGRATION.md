# Integración INDEC - Notas Técnicas

## Estado de la Integración

✅ **Completado**:
- Cliente INDEC completo con 16+ series configuradas
- 5 métodos getter para obtener indicadores (IPC, EMAE, IPI, empleo, ventas, construcción)
- Método de sincronización automática (`sync_all_indicators`)
- Integración con Airflow DAG para sincronización diaria
- Parser mejorado para Excel de patentamientos

⚠️ **Limitaciones Conocidas**:
- **Validación de Series IDs**: No se pudo completar validación en vivo con la API debido a restricciones de red/región (403 Forbidden)
- Los IDs de series fueron obtenidos de la documentación oficial pero no validados con requests reales desde este entorno
- La API es pública y debería funcionar en producción con acceso desde Argentina

## Series Configuradas

### IPC - Índice de Precios al Consumidor
- `ipc_nacional`: IPC Nivel General
- `ipc_alimentos`: IPC Alimentos y Bebidas
- `ipc_transporte`: IPC Transporte (relevante para mercado automotor)
- `ipc_core`: IPC Núcleo (sin estacionales)

### Salarios
- `salario_indice`: Índice General de Salarios
- `salario_privado`: Salario Sector Privado
- `salario_publico`: Salario Sector Público

### Actividad Económica
- `emae`: EMAE - Estimador Mensual Actividad Económica (original)
- `emae_desest`: EMAE Desestacionalizada

### Producción Industrial
- `ipi_general`: Índice de Producción Industrial General
- `ipi_automotriz`: IPI específico de Industria Automotriz ⭐

### Comercio
- `ventas_super`: Ventas en Supermercados
- `ventas_shoppings`: Ventas en Shoppings

### Construcción
- `isac`: Índice Sintético Actividad Construcción

### Empleo
- `empleo_privado`: Índice Trabajadores Registrados Sector Privado

## Fuentes de Datos

### API de Series de Tiempo
- **Endpoint**: `https://apis.datos.gob.ar/series/api/`
- **Documentación**: https://datosgobar.github.io/series-tiempo-ar-api/
- **Portal**: https://datos.gob.ar/series/api
- **Formato**: JSON (también soporta CSV)
- **Rate Limiting**: No especificado en documentación
- **Autenticación**: No requerida (API pública)

### Excel Directo INDEC
- **Base URL**: `https://www.indec.gob.ar/ftp/cuadros/economia/`
- **Archivo patentamientos**: `cuadros_indices_patentamientos.xls`
- **Formato**: Excel (.xls) con múltiples hojas
- **Actualización**: Mensual

## Uso

### Obtener un indicador específico

```python
from backend.api_clients import INDECClient
from datetime import date

client = INDECClient()

# IPC
ipc_data = client.get_ipc(
    fecha_desde=date(2024, 1, 1),
    fecha_hasta=date.today(),
    categoria='nacional'
)

# EMAE
emae_data = client.get_emae(
    fecha_desde=date(2024, 1, 1),
    fecha_hasta=date.today(),
    desestacionalizada=False
)

# IPI Automotriz
ipi_data = client.get_ipi(
    fecha_desde=date(2024, 1, 1),
    fecha_hasta=date.today(),
    sector='automotriz'
)
```

### Sincronización Automática

```python
# Sincronizar últimos 12 meses de todos los indicadores
result = client.sync_all_indicators(meses_atras=12)

# Sincronizar desde fecha específica
result = client.sync_all_indicators(fecha_desde=date(2023, 1, 1))
```

### Integración con Airflow

La sincronización está configurada en el DAG principal:

```python
# airflow/dags/mercado_automotor_etl.py
task_indec = PythonOperator(
    task_id='sync_indec',
    python_callable=sync_indec
)

# Se ejecuta antes del cálculo de indicadores
[task_bcra, task_meli, task_indec] >> task_indicators
```

## Validación de Series

Para validar series en un entorno con acceso a la API:

```bash
# Script standalone
python test_indec_series.py

# Script completo con exploración
python -m backend.scripts.explore_indec_series
```

## Próximos Pasos

1. ✅ Agregar más series económicas (EMAE, IPI, empleo)
2. ⏳ Validar series IDs en producción (requiere acceso desde Argentina)
3. ⏳ Mejorar dashboard con datos INDEC
4. ⏳ Implementar alertas por cambios significativos
5. ⏳ Agregar análisis de correlación entre INDEC y patentamientos

## Referencias

- [API Series de Tiempo - Documentación](https://datosgobar.github.io/series-tiempo-ar-api/)
- [INDEC - Instituto Nacional de Estadística](https://www.indec.gob.ar/)
- [Portal Datos Argentina](https://datos.gob.ar/)
- [Condiciones de Uso API](https://datosgobar.github.io/series-tiempo-ar-api/terms/)

## Notas de Desarrollo

**Fecha**: 2025-11-08

**Cambios Realizados**:
- ✅ Expandido SERIES_IDS de 3 a 16 indicadores
- ✅ Creados 5 métodos getter (get_emae, get_ipi, get_empleo, get_ventas, get_construccion)
- ✅ Implementado método genérico de sincronización (_sync_generic_indicator)
- ✅ Actualizado sync_all_indicators() para incluir todos los indicadores nuevos
- ✅ Mejorado get_patentamientos_excel() con detección automática de headers
- ⚠️ Validación de IDs bloqueada por restricciones de red (403 Forbidden)

**Estructura de Datos**:
- Todos los indicadores se guardan en la tabla `bcra_indicadores` (genérica)
- Campo `indicador` identifica el tipo (ej: 'ipc_nacional', 'emae_original', 'ipi_automotriz')
- Campo `valor` contiene el índice numérico
- Campo `fecha` es la fecha del punto de datos
- Campo `fuente` = 'INDEC'

**Manejo de Errores**:
- Cada método getter retorna `None` en caso de error
- Los métodos de sync retornan dict con 'status': 'success' o 'error'
- sync_all_indicators() captura errores individuales y continúa
- Logs detallados con loguru para debugging
