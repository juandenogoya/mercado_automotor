# Mejoras Implementadas - Pipeline ML de Propensión de Compra

## 📅 Fecha: 17 de Noviembre, 2025

## 🎯 Objetivo
Implementar una metodología robusta de validación cruzada para el modelo de predicción de propensión de compra de marcas automotrices.

---

## ✅ Cambios Implementados

### 1. **Versión LITE de Preparación de Datos** ⚡
**Archivo:** `backend/ml/preparar_datos_propension_lite.py`

**Problema Resuelto:**
- La creación de la tabla `ml_features_propension_compra` con todas las dimensiones tomaba 2-3 horas
- Bloqueaba el desarrollo iterativo del modelo

**Solución:**
- Versión LITE que extrae features directamente desde las vistas KPI LITE existentes
- Usa JOINs para combinar: segmentación demográfica, financiamiento, antigüedad de vehículos, demanda activa
- **Tiempo de ejecución: ~10 segundos** (200x más rápido)
- Genera 23,468 registros con 23 features

**Features Generadas:**
- Demográficas: provincia, marca, año, mes
- Volumen: total_inscripciones, modelos_distintos
- Financiamiento: total_prendas, indice_financiamiento
- Antigüedad: evt_promedio (edad vehículos transferencia), iam_promedio (edad inscripciones)
- Demanda: total_transferencias, indice_demanda_activa
- Tendencias: inscripciones_3m, inscripciones_6m, tendencia_3m, tendencia_6m
- Ratios: ratio_transferencias, ratio_prendas
- Segmentación: edad_promedio, segmento_mercado
- Estacionalidad: mes_sin, mes_cos

**Mejoras Técnicas:**
- ✅ Manejo correcto de tipo_transaccion en kpi_antiguedad_vehiculos_lite (2 JOINs separados)
- ✅ Conversión de columnas categóricas a string antes de fillna('UNKNOWN')
- ✅ Estratificación con fallback para clases raras (< 2 ejemplos)
- ✅ Recomendación de usar TODOS los años disponibles (no solo 2023-2024)

---

### 2. **Script de Entrenamiento con Cross-Validation** 🔬
**Archivo:** `backend/ml/entrenar_modelo_propension_cv.py`

**Motivación del Usuario:**
> "no deberiamos entrenar al menos 3 modelos, para luego hacer un cross valitation?? o metodologias diferentes, para comparar resultados?"

**Implementación:**
- **Stratified K-Fold Cross-Validation** con 5 folds
- Comparación de múltiples modelos: Random Forest vs XGBoost (con opción para LightGBM)
- Métricas estadísticas: Media ± Desviación Estándar en cada métrica
- Grid Search opcional para optimización de hiperparámetros

**Métricas Evaluadas:**
- Accuracy
- Precision (weighted)
- Recall (weighted)
- F1 Score (weighted)
- Top-3 Accuracy (predicción correcta en top 3)
- Top-5 Accuracy (predicción correcta en top 5)

**Arquitectura del Script:**
```
1. Cargar datasets (train/test)
2. Configurar Stratified K-Fold (5 folds)
3. Para cada modelo:
   a. Cross-validation en train set
      - Entrenar en 4 folds
      - Validar en 1 fold
      - Repetir 5 veces
   b. Calcular mean ± std de todas las métricas
   c. Entrenar modelo final en todo el train set
   d. Evaluar en test set (holdout)
4. Comparar modelos
5. Guardar mejor modelo con metadata
```

**Hiperparámetros por Defecto:**
- **Random Forest:**
  - n_estimators: 200
  - max_depth: 20
  - min_samples_split: 5
  - min_samples_leaf: 2
  - class_weight: 'balanced'

- **XGBoost:**
  - n_estimators: 200
  - max_depth: 10
  - learning_rate: 0.1
  - subsample: 0.8
  - colsample_bytree: 0.8

---

### 3. **Correcciones Técnicas Críticas** 🔧

#### 3.1. Labels en top_k_accuracy_score - Cross-Validation
**Problema:**
```
ValueError: Number of given labels (100) not equal to the number of classes in 'y_score' (91)
```

**Causa:**
Cada fold de CV puede tener diferente número de clases presentes. Pasar `labels` fijo causaba error.

**Solución:**
```python
# ❌ INCORRECTO
'top3_accuracy': make_scorer(top_k_accuracy_score, k=3, labels=all_labels)

# ✅ CORRECTO
'top3_accuracy': make_scorer(top_k_accuracy_score, k=3)  # sklearn maneja automáticamente
```

#### 3.2. Labels en Evaluación Final del Modelo
**Problema:**
```
ValueError: Number of given labels (100) not equal to the number of classes in 'y_score' (96)
```

**Causa:**
El modelo solo aprende las clases que ve durante entrenamiento (96), pero `encoders['target'].classes_` contiene todas las posibles (100). Las 4 clases faltantes son marcas con solo 1 ejemplo.

**Solución:**
```python
# ❌ INCORRECTO
all_labels = np.arange(len(encoders['target'].classes_))
top3_acc = top_k_accuracy_score(y_test, y_pred_proba, k=3, labels=all_labels)

# ✅ CORRECTO
model_labels = model.classes_  # Solo las clases que el modelo conoce
top3_acc = top_k_accuracy_score(y_test, y_pred_proba, k=3, labels=model_labels)
```

#### 3.3. Documentación - Usar Todos los Años
**Archivo:** `backend/ml/README.md`

**Cambio:**
```bash
# ❌ ANTES (solo 2 años)
python backend/ml/preparar_datos_propension.py --output data/ml/ --anios 2023,2024

# ✅ AHORA (todos los años disponibles)
python backend/ml/preparar_datos_propension.py --output data/ml/
```

**Beneficios:**
- Mayor precisión del modelo (más datos)
- Captura de tendencias de largo plazo
- Mejor detección de estacionalidad
- Reduce sobreajuste (overfitting)

---

## 📊 Resultados Esperados

### Datasets Generados (Versión LITE)
- **Total registros:** 23,468
- **Marcas únicas:** 100
- **Años de datos:** 7 (2019-2025)
- **Total inscripciones:** ~2.8M
- **Train set:** 18,774 muestras (80%)
- **Test set:** 4,694 muestras (20%)
- **Features:** 23

### Rendimiento Preliminar (Random Forest)
_Basado en corridas parciales antes del fix final:_
- **Cross-Validation (5 folds):**
  - Accuracy: 0.7069 ± 0.0056
  - F1 Weighted: 0.7010 ± 0.0058
  - Tiempo: ~13.56 segundos

- **Observación:**
  - Train accuracy: 1.0000 (indica posible overfitting)
  - Podría beneficiarse de regularización adicional o poda

---

## 🚀 Próximos Pasos

### Para Ejecutar el Pipeline Completo:

1. **Preparar Datos:**
```bash
python backend/ml/preparar_datos_propension_lite.py --output data/ml/
```

2. **Entrenar con Cross-Validation:**
```bash
# Versión básica (sin grid search)
python backend/ml/entrenar_modelo_propension_cv.py --input data/ml/

# Con optimización de hiperparámetros (más lento)
python backend/ml/entrenar_modelo_propension_cv.py --input data/ml/ --grid-search

# Solo Random Forest (más rápido)
python backend/ml/entrenar_modelo_propension_cv.py --input data/ml/ --only-rf
```

3. **Revisar Resultados:**
- Modelos guardados en: `data/models/propension_compra_cv/`
- Archivos generados:
  - `{model_name}_modelo.joblib` - Modelo entrenado
  - `{model_name}_encoders.pkl` - Encoders de features
  - `{model_name}_metadata.json` - Métricas y configuración
  - `feature_importance.png` - Importancia de features (si disponible)

---

## 📝 Requisitos del Sistema

### Dependencias Python:
```bash
pip install -r requirements_ml.txt
```

### Acceso a Base de Datos:
- PostgreSQL 13+ corriendo en localhost:5432
- Base de datos: `mercado_automotor`
- Vistas KPI LITE creadas y actualizadas:
  - kpi_segmentacion_demografica_lite
  - kpi_financiamiento_lite
  - kpi_antiguedad_vehiculos_lite
  - kpi_demanda_activa_lite

---

## 🎓 Metodología Implementada

### ¿Por qué Cross-Validation?
1. **Evaluación más robusta:** Cada dato participa en validación una vez
2. **Reduce varianza:** Promedio de 5 evaluaciones independientes
3. **Detecta overfitting:** Compara train vs validation en cada fold
4. **Estabilidad:** Desviación estándar indica consistencia del modelo

### ¿Por qué Stratified?
- Mantiene la proporción de cada clase (marca) en cada fold
- Crítico para datasets desbalanceados (algunas marcas tienen pocas inscripciones)
- Previene folds con clases no representadas

### ¿Por qué Top-K Accuracy?
En recomendaciones comerciales, no solo importa la predicción exacta:
- **Top-3:** ¿La marca correcta está en las 3 recomendaciones principales?
- **Top-5:** ¿La marca correcta está en las 5 recomendaciones principales?
- Más realista para casos de uso de marketing y recomendación

---

## 🔍 Archivos Modificados

### Creados:
- `backend/ml/preparar_datos_propension_lite.py` - Versión rápida de preparación
- `backend/ml/entrenar_modelo_propension_cv.py` - Entrenamiento con CV

### Modificados:
- `backend/ml/README.md` - Documentación actualizada con mejores prácticas
- `backend/ml/preparar_datos_propension.py` - Docstrings actualizados
- `backend/ml/entrenar_modelo_propension.py` - Fix de labels en top_k_accuracy_score
- `Iniciar_Dashboard_Mercado_Automotor.bat` - Corrección de puerto Ngrok

### Scripts de Utilidad:
- `backend/scripts/analizar_años_disponibles.py` - Analizar años en DB (creado, no ejecutado)

---

## 💡 Lecciones Aprendidas

1. **Performance vs Completeness:**
   - A veces es mejor iterar rápido con features esenciales (LITE)
   - Luego expandir a features completas cuando el modelo base funciona

2. **Class Imbalance:**
   - Algunas marcas tienen muy pocos ejemplos (<2)
   - Estratificación puede fallar → necesario fallback sin stratify
   - El modelo no aprenderá clases que no ve en train

3. **Sklearn Labels Parameter:**
   - En CV: NO pasar labels (cada fold es diferente)
   - En evaluación final: usar `model.classes_` no `encoder.classes_`

4. **Validación del Usuario es Valiosa:**
   - Usuario sugirió CV y comparación de modelos → gran mejora metodológica
   - Usuario cuestionó usar solo 2 años → ahora usamos todos

---

## 📧 Contacto y Soporte

Para preguntas sobre esta implementación:
- Ver documentación: `backend/ml/README.md`
- Revisar logs de entrenamiento en: `data/models/propension_compra_cv/*.json`
- Código fuente comentado en detalle

---

_Documento generado: 2025-11-17_
_Última actualización: Commit 1179ddb_
