# 🤖 Fase 4: Modelos de Forecasting

Sistema completo de entrenamiento y comparación de modelos para forecasting de operaciones del mercado automotor.

---

## 🎯 Objetivo

Entrenar y comparar 2 modelos complementarios:
1. **Prophet** - Series temporales con estacionalidad (Facebook)
2. **XGBoost** - Gradient Boosting con múltiples features

**Target:** Predecir `total_operaciones` mensuales (inscripciones + transferencias + prendas)

---

## 📋 Prerequisitos

### 1. Dataset Unificado

Debe existir: `data/processed/dataset_forecasting_completo.parquet`

Si no existe, ejecutar:
```powershell
python backend/data_processing/ejecutar_pipeline_completa.py
```

### 2. Dependencias Python

```powershell
# Instalar dependencias de modelos
pip install -r backend/models/requirements_models.txt
```

**Librerías requeridas:**
- `prophet>=1.1.5`
- `xgboost>=2.0.0`
- `scikit-learn>=1.3.0`
- `pandas`, `numpy`, `pyarrow`

---

## 🚀 Uso Rápido

### Opción A: Entrenar y Comparar Ambos Modelos (RECOMENDADO) ⚡

```powershell
# Desde: mercado_automotor/
python backend/models/comparar_modelos.py
```

Esto ejecuta:
1. ✅ Entrena Prophet (~30 seg)
2. ✅ Entrena XGBoost (~20 seg)
3. ✅ Compara métricas
4. ✅ Genera reporte comparativo

**Tiempo total:** ~1 minuto

---

### Opción B: Entrenar Modelos Individualmente

```powershell
# Solo Prophet
python backend/models/train_prophet.py

# Solo XGBoost
python backend/models/train_xgboost.py
```

---

## 📊 Modelos Implementados

### 1. Prophet 📈

**Descripción:**
Modelo de Facebook diseñado para series temporales de negocios con estacionalidad fuerte.

**Características:**
- Maneja estacionalidad automáticamente (mensual, anual)
- Robusto a valores faltantes y outliers
- Interpreta componentes: tendencia + estacionalidad
- Puede incluir regresores externos (variables BCRA/INDEC)

**Configuración:**
```python
{
  'seasonality_mode': 'multiplicative',
  'yearly_seasonality': True,
  'changepoint_prior_scale': 0.05,
  'regresores': ['IPC', 'EMAE', 'TC', ...]  # Top 8 variables
}
```

**Features utilizadas:**
- Target: `total_operaciones`
- Regresores: Top 5 BCRA + Top 3 INDEC

---

### 2. XGBoost 🚀

**Descripción:**
Gradient Boosting avanzado que maneja múltiples features y relaciones complejas.

**Características:**
- Usa TODAS las ~100 features del dataset
- Captura relaciones no-lineales
- Feature importance para interpretabilidad
- Early stopping para evitar overfitting

**Configuración:**
```python
{
  'n_estimators': 1000,
  'max_depth': 6,
  'learning_rate': 0.05,
  'subsample': 0.8,
  'colsample_bytree': 0.8,
  'early_stopping_rounds': 50
}
```

**Features utilizadas:**
- ~100 features numéricas:
  - Operaciones (4)
  - Top provincias (5) y marcas (5)
  - Variables BCRA (11)
  - Variables INDEC (5)
  - Features temporales (7)
  - Lags: 1, 3, 6, 12 meses (12)
  - Rolling means: 3, 6, 12 meses (9)
  - Features avanzadas: ratios, tendencias (5+)

---

## 📊 Estrategia de Evaluación

### Split Temporal (NO aleatorio)

```
Total: 80 meses

Train:      60 meses (75%)   → Entrenar modelos
Validation: 10 meses (12.5%) → Tuning y early stopping
Test:       10 meses (12.5%) → Evaluación final
```

**Importante:** Split cronológico, NO aleatorio.

### Métricas de Evaluación

```
┌─────────┬───────────────────────────────────────────┐
│ Métrica │ Descripción                               │
├─────────┼───────────────────────────────────────────┤
│ RMSE    │ Root Mean Squared Error (penaliza grandes errores) │
│ MAE     │ Mean Absolute Error (error promedio)     │
│ MAPE    │ Mean Absolute Percentage Error (% error) │
│ R²      │ Coeficiente de determinación (ajuste)    │
└─────────┴───────────────────────────────────────────┘
```

**Todas se calculan en:** Train, Validation y Test

---

## 📁 Archivos Generados

### Estructura de Output

```
mercado_automotor/
├── models/
│   ├── prophet_model.pkl          # Modelo Prophet entrenado
│   └── xgboost_model.pkl          # Modelo XGBoost entrenado
│
└── results/
    ├── prophet/
    │   ├── predictions.parquet    # Predicciones (fecha, real, pred, bounds)
    │   ├── metrics.json           # Métricas (train/val/test)
    │   └── components.parquet     # Componentes Prophet (tendencia, estacionalidad)
    │
    ├── xgboost/
    │   ├── predictions.parquet    # Predicciones (fecha, real, pred)
    │   ├── metrics.json           # Métricas (train/val/test)
    │   └── feature_importance.parquet  # Importancia de features
    │
    └── comparison/
        ├── comparison_metrics.json     # Comparación completa
        └── comparison_report.txt       # Reporte textual
```

---

## 📊 Ejemplo de Reporte de Comparación

```
================================================================================
REPORTE COMPARATIVO: PROPHET VS XGBOOST
================================================================================

📊 MÉTRICAS EN TEST:
--------------------------------------------------------------------------------
Métrica         |         Prophet |         XGBoost |        Mejor |    Dif %
--------------------------------------------------------------------------------
RMSE            |        1,250.00 |        1,100.00 |      XGBoost |     12.0%
MAE             |          950.00 |          850.00 |      XGBoost |     10.5%
MAPE            |           8.50% |           7.20% |      XGBoost |     15.3%
R2              |          0.8200 |          0.8700 |      XGBoost |      6.1%
--------------------------------------------------------------------------------

🎯 RECOMENDACIÓN

✅ XGBOOST es el modelo recomendado (4/4 métricas)

Motivos:
  - Mejor performance en todas las métricas
  - Captura relaciones complejas entre features
  - Feature importance para interpretabilidad
```

---

## 🔍 Análisis Post-Entrenamiento

### 1. Ver Métricas

```python
import json

# Prophet
with open('results/prophet/metrics.json') as f:
    prophet_metrics = json.load(f)
    print(prophet_metrics['Test'])

# XGBoost
with open('results/xgboost/metrics.json') as f:
    xgboost_metrics = json.load(f)
    print(xgboost_metrics['Test'])
```

### 2. Ver Predicciones

```python
import pandas as pd

# Prophet
df_prophet = pd.read_parquet('results/prophet/predictions.parquet')
print(df_prophet.head())

# XGBoost
df_xgboost = pd.read_parquet('results/xgboost/predictions.parquet')
print(df_xgboost.head())
```

### 3. Feature Importance (XGBoost)

```python
df_importance = pd.read_parquet('results/xgboost/feature_importance.parquet')
print(df_importance.head(20))  # Top 20 features
```

### 4. Componentes (Prophet)

```python
df_components = pd.read_parquet('results/prophet/components.parquet')
# Columnas: ds, trend, yearly, yhat, yhat_lower, yhat_upper
print(df_components[['ds', 'trend', 'yearly', 'yhat']].head())
```

---

## 🎨 Próximas Mejoras (Opcional)

### 1. Visualizaciones

Crear gráficos de:
- Predicciones vs Real (línea temporal)
- Error por mes (barras)
- Componentes Prophet
- Feature importance XGBoost
- Distribución de errores

### 2. Ensemble

Combinar ambos modelos:
```python
pred_ensemble = 0.6 * pred_xgboost + 0.4 * pred_prophet
```

### 3. Hiperparámetro Tuning

Usar GridSearch o Optuna para optimizar:
- Prophet: `changepoint_prior_scale`, `seasonality_prior_scale`
- XGBoost: `max_depth`, `learning_rate`, `n_estimators`

### 4. Modelos Adicionales

- LightGBM (más rápido que XGBoost)
- CatBoost (maneja categóricas mejor)
- LSTM (deep learning para series temporales)

---

## 🐛 Troubleshooting

### Error: "Prophet no está instalado"
```powershell
pip install prophet
```

**Nota Windows:** Prophet requiere compilador C++. Si falla:
```powershell
conda install -c conda-forge prophet
```

### Error: "XGBoost no está instalado"
```powershell
pip install xgboost
```

### Error: "Dataset no encontrado"
Ejecutar pipeline completa primero:
```powershell
python backend/data_processing/ejecutar_pipeline_completa.py
```

### Advertencia: "Convergence warnings" (Prophet)
Normal, no afecta performance. Prophet ajusta automáticamente.

---

## 📈 Interpretación de Resultados

### ¿Qué métricas importan más?

1. **MAPE** - Error porcentual, fácil de interpretar
   - < 10%: Excelente
   - 10-20%: Bueno
   - > 20%: Necesita mejora

2. **R²** - Qué % de varianza explica el modelo
   - > 0.8: Muy bueno
   - 0.6-0.8: Bueno
   - < 0.6: Necesita mejora

3. **RMSE/MAE** - En escala del target
   - Comparar con media/std del target

### ¿Cuándo usar cada modelo?

**Usar Prophet si:**
- Necesitas interpretabilidad (tendencia + estacionalidad)
- Hay cambios de régimen (eventos especiales)
- Datos con valores faltantes
- Forecasting a largo plazo

**Usar XGBoost si:**
- Tienes muchas features predictoras
- Relaciones complejas entre variables
- Necesitas máxima precisión
- Forecasting a corto/mediano plazo

**Usar Ensemble:**
- Cuando ambos tienen performance similar
- Para reducir riesgo y varianza

---

## 📞 Soporte

Si encuentras problemas:
1. Verifica que el dataset existe
2. Verifica dependencias instaladas
3. Revisa logs de entrenamiento
4. Chequea métricas en validation (puede haber overfitting)

---

**Última actualización:** 2025-11-12
**Versión:** 1.0
