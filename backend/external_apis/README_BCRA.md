# Cliente BCRA - Banco Central de la República Argentina

## 📋 Descripción

Cliente Python para acceder a datos macroeconómicos del BCRA a través de la API pública.

**API utilizada:** https://api.estadisticasbcra.com/

---

## 🎯 Variables Disponibles

| Variable | Descripción | Unidad |
|----------|-------------|--------|
| `inflacion_mensual_oficial` | IPC Mensual | % |
| `inflacion_interanual_oficial` | IPC Interanual | % |
| `usd` | Tipo de Cambio USD Oficial | ARS/USD |
| `usd_of` | Tipo de Cambio USD Informal (blue) | ARS/USD |
| `var_usd_vs_usd_of` | Spread oficial vs informal | % |
| `tasa_badlar` | Tasa BADLAR | % |
| `tasa_leliq` | Tasa LELIQ | % |
| `reservas` | Reservas Internacionales | Millones USD |
| `base_monetaria` | Base Monetaria | Millones ARS |
| `circulacion_monetaria` | Circulación Monetaria | Millones ARS |
| `depositos` | Depósitos Totales | Millones ARS |
| `plazo_fijo` | Depósitos a Plazo Fijo | Millones ARS |

---

## 🚀 Uso Rápido

### **Opción 1: Usar el script de descarga (recomendado)**

```bash
# Desde: mercado_automotor/
python backend/data_processing/04_obtener_datos_bcra.py
```

**Esto descarga:**
- Datos desde 2019-01-01 hasta hoy
- Guarda en formato Parquet (optimizado)
- Genera datasets diarios y mensuales

**Archivos generados:**
```
data/processed/
├── bcra_datos_diarios.parquet         # Datos originales (diarios)
├── bcra_datos_mensuales.parquet       # Agregado mensual (para forecasting)
├── bcra_datos_diarios_sample.csv      # Muestra (primeros 100)
└── bcra_datos_mensuales_sample.csv    # Muestra
```

---

### **Opción 2: Usar el cliente directamente**

```python
from backend.external_apis.bcra_client import BCRAClient

# Crear cliente
client = BCRAClient()

# Obtener una variable
df_usd = client.get_series('usd', fecha_desde='2020-01-01', fecha_hasta='2025-12-31')

# Obtener múltiples variables
df_multiple = client.get_multiple_series(
    variables=['usd', 'inflacion_mensual_oficial', 'tasa_badlar'],
    fecha_desde='2020-01-01',
    format='wide'  # 'wide' = una columna por variable, 'long' = apiladas
)

# Obtener último valor
ultimo_usd = client.get_latest_value('usd')
print(f"USD hoy: ${ultimo_usd}")

# Ver variables disponibles
client.print_available_variables()
```

---

## 📊 Formato de Datos

### **Datos diarios:**

| fecha | inflacion_mensual_oficial | usd | tasa_badlar | reservas | ... |
|-------|---------------------------|-----|-------------|----------|-----|
| 2019-01-01 | 2.9 | 37.5 | 47.5 | 65000 | ... |
| 2019-01-02 | 2.9 | 37.8 | 47.5 | 65100 | ... |
| ... | ... | ... | ... | ... | ... |

### **Datos mensuales (agregado):**

| fecha | inflacion_mensual_oficial | usd | tasa_badlar | reservas | anio | mes | trimestre |
|-------|---------------------------|-----|-------------|----------|------|-----|-----------|
| 2019-01-01 | 2.9 | 37.6 | 47.5 | 65050 | 2019 | 1 | 1 |
| 2019-02-01 | 3.8 | 38.2 | 48.1 | 64800 | 2019 | 2 | 1 |
| ... | ... | ... | ... | ... | ... | ... | ... |

---

## 🔧 Configuración Avanzada

### **Cambiar rango de fechas:**

Editar `backend/data_processing/04_obtener_datos_bcra.py`, línea ~250:

```python
FECHA_DESDE = '2015-01-01'  # Cambiar aquí
FECHA_HASTA = '2023-12-31'  # O None para hoy
```

### **Seleccionar solo algunas variables:**

Editar `backend/data_processing/04_obtener_datos_bcra.py`, línea ~40:

```python
variables = [
    'inflacion_mensual_oficial',  # Mantener solo las que necesites
    'usd',
    'tasa_badlar'
]
```

---

## 📈 Variables Recomendadas para Forecasting Automotor

**Prioridad ALTA** (impacto directo):
- ✅ `inflacion_mensual_oficial` - Poder adquisitivo
- ✅ `inflacion_interanual_oficial` - Tendencia inflacionaria
- ✅ `usd` - Costo de vehículos importados
- ✅ `tasa_badlar` - Costo de financiamiento

**Prioridad MEDIA** (contexto macro):
- ⚠️ `var_usd_vs_usd_of` - Incertidumbre cambiaria
- ⚠️ `reservas` - Estabilidad macro
- ⚠️ `depositos` - Liquidez del mercado

**Prioridad BAJA** (opcional):
- 🔹 `base_monetaria` - Contexto monetario
- 🔹 `circulacion_monetaria`
- 🔹 `plazo_fijo`

---

## ⚠️ Limitaciones

1. **Frecuencia de actualización:**
   - Datos diarios para tipo de cambio y tasas
   - Datos mensuales para inflación
   - Puede haber delay de 1-2 días

2. **Datos faltantes:**
   - Algunas variables tienen gaps históricos
   - El script maneja automáticamente valores nulos

3. **Rate limiting:**
   - La API tiene límites de requests
   - El cliente implementa retry con exponential backoff

---

## 🐛 Troubleshooting

### **Error: "Connection refused"**

**Problema:** Sin conexión a internet o API caída.

**Solución:**
```python
# Verificar conectividad
import requests
response = requests.get('https://api.estadisticasbcra.com/usd')
print(response.status_code)  # Debe ser 200
```

### **Error: "Variable no válida"**

**Problema:** Variable no existe o nombre incorrecto.

**Solución:**
```python
# Ver variables disponibles
from backend.external_apis.bcra_client import BCRAClient
client = BCRAClient()
client.print_available_variables()
```

### **Datos vacíos para cierto período**

**Problema:** La API no tiene datos para ese rango.

**Solución:** Ajustar fechas o usar interpolación para llenar gaps.

---

## 📝 Próximos Pasos

1. ✅ **Completado:** Cliente BCRA funcional
2. ⏳ **Siguiente:** Cliente INDEC (EMAE, Desempleo)
3. ⏳ **Después:** Scraper CEM (CCL, Liquidaciones)
4. ⏳ **Final:** Combinar todos los datasets macro

---

## 📧 Referencias

- **API BCRA (no oficial):** https://estadisticasbcra.com/
- **Documentación:** https://estadisticasbcra.com/api/documentacion
- **API oficial BCRA:** https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp

---

**Fecha:** 2025-11-12
**Versión:** 1.0
**Autor:** Claude + Usuario
