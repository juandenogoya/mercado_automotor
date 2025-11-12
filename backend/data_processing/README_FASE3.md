# 📊 Fase 3: Unificación de Datasets para Forecasting

Sistema completo para generar un dataset unificado listo para entrenar modelos de forecasting.

---

## 🎯 Objetivo

Unificar 3 fuentes de datos en un dataset mensual completo:
1. **Dataset transaccional** - Inscripciones + Transferencias + Prendas (17M+ registros)
2. **Datos BCRA** - Variables macroeconómicas (IPC, TC, BADLAR, etc.)
3. **Datos INDEC** - Actividad económica y mercado laboral (EMAE, Desocupación, etc.)

**Output final:** `data/processed/dataset_forecasting_completo.parquet`

---

## 🚀 Uso Rápido

### Opción A: Pipeline Completa (Recomendado) ⚡

Ejecuta TODO en un solo comando:

```powershell
# Desde: mercado_automotor/
python backend/data_processing/ejecutar_pipeline_completa.py
```

**Esto ejecuta:**
1. Unifica dataset transaccional (~5 min)
2. Descarga datos BCRA (~30 seg)
3. Descarga datos INDEC (~30 seg)
4. Unifica todo para forecasting (~1 min)

**Tiempo total:** ~7 minutos

---

### Opción B: Paso a Paso (Control Manual)

Si prefieres ejecutar cada paso manualmente:

```powershell
# Paso 1: Dataset transaccional (~5 min)
python backend/data_processing/02_unir_datasets_v3.py

# Paso 2: Datos BCRA (~30 seg)
python backend/data_processing/04_obtener_datos_bcra_v2.py

# Paso 3: Datos INDEC (~30 seg)
python backend/data_processing/05_obtener_datos_indec.py

# Paso 4: Unificación final (~1 min)
python backend/data_processing/07_unificar_datasets_forecasting.py
```

---

## 📋 Scripts Disponibles

### `ejecutar_pipeline_completa.py` 🌟
**Script maestro que orquesta toda la pipeline**

```powershell
# Pipeline completa
python backend/data_processing/ejecutar_pipeline_completa.py

# Solo dataset transaccional
python backend/data_processing/ejecutar_pipeline_completa.py --solo-transaccional

# Solo APIs (BCRA + INDEC)
python backend/data_processing/ejecutar_pipeline_completa.py --solo-apis

# Datasets base sin unificar
python backend/data_processing/ejecutar_pipeline_completa.py --sin-unificacion
```

### `07_unificar_datasets_forecasting.py`
**Script de unificación (Fase 3 principal)**

Realiza:
- Agregación mensual del dataset transaccional
- Features de top provincias y marcas
- Merge con datos BCRA y INDEC
- Features temporales (año, mes, sin/cos)
- **Lags:** 1, 3, 6, 12 meses
- **Rolling means:** 3, 6, 12 meses
- **Features avanzadas:** ratios, tendencias, interacciones

```powershell
python backend/data_processing/07_unificar_datasets_forecasting.py
```

### `06_analizar_datasets_para_merge.py`
**Script de análisis exploratorio**

Analiza estructura de los 3 datasets antes de unificarlos.

```powershell
python backend/data_processing/06_analizar_datasets_para_merge.py
```

---

## 📊 Dataset Final

### Ubicación
```
data/processed/dataset_forecasting_completo.parquet
```

### Contenido

**Dimensiones:**
- ~80+ registros mensuales (2019-2025)
- ~100+ features

**Categorías de features:**

1. **Operaciones transaccionales (3)**
   - `total_inscripciones`
   - `total_transferencias`
   - `total_prendas`
   - `total_operaciones` (suma)

2. **Top Provincias (5)**
   - Operaciones por provincia (top 5 por volumen)

3. **Top Marcas (5)**
   - Operaciones por marca (top 5 por volumen)

4. **Variables BCRA (~11)**
   - IPC mensual/interanual
   - Tipo de cambio USD/ARS
   - BADLAR, LELIQ
   - Reservas internacionales
   - Base monetaria, circulación, depósitos

5. **Variables INDEC (5)**
   - EMAE (actividad económica)
   - Tasa de desocupación
   - Tasa de actividad
   - Tasa de empleo
   - RIPTE (salarios)

6. **Features temporales (7)**
   - año, mes, trimestre
   - mes_sin, mes_cos (cíclicos)
   - trimestre_sin, trimestre_cos (cíclicos)

7. **Lags - 3 variables × 4 períodos (12)**
   - `total_operaciones_lag_1/3/6/12`
   - `total_inscripciones_lag_1/3/6/12`
   - `total_transferencias_lag_1/3/6/12`

8. **Rolling means - 3 variables × 3 ventanas (9)**
   - `total_operaciones_rolling_3/6/12`
   - `total_inscripciones_rolling_3/6/12`
   - `total_transferencias_rolling_3/6/12`

9. **Features avanzadas (~5)**
   - `ratio_insc_transf`
   - `var_mensual_operaciones`
   - `var_mensual_operaciones_abs`
   - `tendencia_operaciones`
   - `interaccion_operaciones_emae`

---

## 🔍 Ejemplo de Uso del Dataset Final

```python
import pandas as pd

# Cargar dataset
df = pd.read_parquet('data/processed/dataset_forecasting_completo.parquet')

print(f"Registros: {len(df)}")
print(f"Features: {len(df.columns)}")
print(f"Período: {df['fecha'].min()} a {df['fecha'].max()}")

# Ver primeras filas
print(df.head())

# Features disponibles
print(df.columns.tolist())

# Preparar para forecasting
X = df.drop(['fecha', 'total_operaciones'], axis=1)  # Features
y = df['total_operaciones']  # Target

# Entrenar modelo
from sklearn.ensemble import RandomForestRegressor
modelo = RandomForestRegressor()
modelo.fit(X, y)
```

---

## ⚠️ Prerequisitos

Antes de ejecutar la Fase 3, asegúrate de tener:

1. **Base de datos PostgreSQL** con datos de datos.gob.ar:
   - Tabla: `datos_gob_inscripciones`
   - Tabla: `datos_gob_transferencias`
   - Tabla: `datos_gob_prendas`

2. **Conexión a internet** para descargar BCRA e INDEC

3. **Espacio en disco**: ~500 MB libres en `data/processed/`

---

## 📈 Próximos Pasos (Fase 4)

Una vez tengas el dataset unificado, puedes:

1. **Entrenar modelos de forecasting**
   - Prophet (series temporales)
   - XGBoost (gradient boosting)
   - LSTM (deep learning)
   - ARIMA/SARIMA

2. **Análisis exploratorio avanzado**
   - Correlaciones entre variables
   - Importancia de features
   - Análisis de estacionalidad

3. **Validación y métricas**
   - Train/test split temporal
   - Cross-validation temporal
   - RMSE, MAE, MAPE

4. **Integración con dashboard**
   - Agregar pestaña de forecasting
   - Visualizar predicciones vs reales
   - Análisis de escenarios

---

## 🐛 Troubleshooting

### Error: "Archivo no encontrado"
**Solución:** Ejecuta primero los scripts base (02, 04, 05)

```powershell
python backend/data_processing/ejecutar_pipeline_completa.py
```

### Error: "psycopg2 encoding"
**Solución:** Ya está resuelto en script V3, usa la estructura correcta de imports

### Pipeline tarda mucho
**Normal:** El paso de dataset transaccional toma ~5 minutos (17M registros)

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs detallados de cada script
2. Verifica que las tablas PostgreSQL existan
3. Asegura conexión a internet para APIs
4. Verifica espacio en disco disponible

---

**Última actualización:** 2025-11-12
**Versión:** 1.0
