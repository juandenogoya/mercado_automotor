# Instrucciones: Agregación Semanal de Datos

## 🎯 Objetivo
Convertir el dataset mensual (81 registros) a semanal (~324 registros) para mejorar el entrenamiento del modelo.

## 📋 Pasos a Seguir

### 1. Verificar que tengas los datos necesarios

En tu máquina Windows, ejecutá:

```powershell
python -c "import os; print('Dataset transaccional:', os.path.exists('data/processed/dataset_transaccional_unificado.parquet')); print('BCRA:', os.path.exists('data/processed/bcra_datos_mensuales.parquet')); print('INDEC:', os.path.exists('data/processed/indec_datos_mensuales.parquet'))"
```

**Si los 3 muestran `True`** → Continúa al paso 2

**Si alguno muestra `False`** → Ejecutá primero el pipeline completo:
```powershell
python backend/data_processing/ejecutar_pipeline_completa.py
```

### 2. Ejecutar la agregación semanal

```powershell
python backend/data_processing/07b_unificar_datasets_forecasting_semanal.py
```

**Tiempo estimado:** ~2-3 minutos

**Resultado esperado:**
```
✅ UNIFICACIÓN SEMANAL COMPLETADA

📊 Dataset final:
   - Registros (semanas): ~324
   - Columnas: ~60-70
   - Período: 2019-01-01 a 2025-09-01
   - Target media: ~12,000-15,000
```

### 3. Modificar el modelo para usar datos semanales

Editá `backend/models/train_xgboost_optimizado.py`:

**CAMBIAR LÍNEA 33:**
```python
# ANTES (mensual - 81 registros)
INPUT_FILE = 'data/processed/dataset_forecasting_completo.parquet'

# DESPUÉS (semanal - ~324 registros)
INPUT_FILE = 'data/processed/dataset_forecasting_completo_semanal.parquet'
```

### 4. Entrenar el modelo con datos semanales

```powershell
python backend/models/train_xgboost_optimizado.py
```

**Resultado esperado:**
```
📊 Dataset cargado:
   - Registros: ~324    ← 4x más datos que mensual
   - Columnas: ~60-70

📊 Top 15 features seleccionadas:
   operaciones_buenos_aires    | 0.XXXX
   operaciones_córdoba         | 0.XXXX
   ...

📊 Train:     ~243 registros (75%)
📊 Validation: ~40 registros (12.5%)
📊 Test:       ~41 registros (12.5%)

✅ Modelo bien generalizado (gap < 0.15)  ← OBJETIVO
```

## 🎯 Mejoras Esperadas

Con ~324 registros semanales vs 81 mensuales:

| Métrica | Mensual (81) | Semanal (~324) | Mejora |
|---------|--------------|----------------|--------|
| **Registros train** | 60 | ~243 | **4x más** |
| **Registros test** | 11 | ~41 | **4x más** |
| **Gap Train-Test** | > 3.0 (malo) | < 0.30 (bueno) | **✅ Mejor generalización** |
| **R² Test** | Negativo | Positivo | **✅ Modelo útil** |

## ⚠️ Notas Importantes

1. **Lags ajustados:** Los lags están en semanas (1, 2, 4, 8, 12) en lugar de meses
2. **Rolling means:** Windows de 4, 8, 12 semanas (≈ 1, 2, 3 meses)
3. **Variables BCRA/INDEC:** Se interpolan linealmente de mensual a semanal
4. **Interpretación:** Ahora predecís operaciones por **semana**, no por mes

## 🐛 Troubleshooting

### Error: "Archivo no encontrado"
→ Ejecutá el pipeline completo primero (paso 1)

### Error: "ModuleNotFoundError: pyarrow"
```powershell
pip install pyarrow pandas
```

### El modelo sigue con overfitting
→ Probá el modelo ultra simple (solo 5 features):
```powershell
python backend/models/train_xgboost_ultra_simple.py
```
(Este auto-ajusta el número de features según el tamaño del dataset)

## 📊 Comparación de Resultados

Después de entrenar, compará con el resultado mensual:

```powershell
# Ver resultados del modelo optimizado
type results\xgboost_optimized\metrics.json

# O leer el último output de la consola
```

Buscá en el output:
- **R² Test** debe ser > 0 (idealmente > 0.70)
- **Gap Train-Test** debe ser < 0.30
- Si dice "✅ Modelo bien generalizado" → Éxito!

## 🚀 Siguiente Paso (Opcional)

Si los resultados son buenos, podés integrar el forecasting al dashboard:
1. Guardar las predicciones semanales
2. Agregar un nuevo tab "Predicción de Operaciones"
3. Mostrar forecast para las próximas 4-12 semanas
