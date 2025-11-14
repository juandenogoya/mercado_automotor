# 🤖 Pipeline de Machine Learning - Mercado Automotor

Pipeline completo de análisis predictivo para predecir la demanda de vehículos en Argentina integrando variables macro-económicas.

---

## 📋 Índice

1. [Objetivo](#objetivo)
2. [Datasets Utilizados](#datasets-utilizados)
3. [Pipeline de Trabajo](#pipeline-de-trabajo)
4. [Modelos Implementados](#modelos-implementados)
5. [Ejecución](#ejecución)
6. [Resultados Esperados](#resultados-esperados)
7. [Uso de Predicciones](#uso-de-predicciones)

---

## 🎯 Objetivo

**Predecir la demanda mensual de vehículos** (cantidad de transacciones) por marca, modelo y provincia, considerando variables macro-económicas para evaluar cómo factores económicos afectan el mercado automotriz.

### Variable Target
- **`cantidad_transacciones`**: Volumen mensual de transacciones por marca/modelo/provincia/tipo

### Casos de Uso
1. **Planificación de inventario**: Proyectar demanda futura por marca/modelo
2. **Análisis de sensibilidad**: Evaluar impacto de variables macro (IPC, BADLAR, TC)
3. **Estrategia comercial**: Identificar oportunidades por provincia/segmento
4. **Evaluación de escenarios**: Simular demanda bajo diferentes condiciones económicas

---

## 📊 Datasets Utilizados

### Datasets Transaccionales (DNRPA - datos.gob.ar)
- **`datos_gob_inscripciones`**: Inscripciones iniciales 0km (~3M registros)
- **`datos_gob_transferencias`**: Transferencias vehículos usados (~9M registros)
- **`datos_gob_prendas`**: Prendas vehículos financiados (~2M registros)

**Variables clave**:
- `tramite_fecha`: Fecha de la transacción
- `automotor_marca_descripcion`: Marca del vehículo
- `automotor_modelo_descripcion`: Modelo del vehículo
- `registro_seccional_provincia`: Provincia
- `titular_genero`: Género del titular
- `titular_anio_nacimiento`: Año de nacimiento (para calcular edad)
- `automotor_anio_modelo`: Año del modelo

### Datasets Macro-económicos
- **`ipc`**: Índice de Precios al Consumidor (INDEC)
  - `nivel_general`, `variacion_mensual`, `variacion_interanual`

- **`badlar`**: Tasa BADLAR (BCRA)
  - Promedio mensual y volatilidad

- **`tipo_cambio`**: Tipo de cambio oficial (BCRA)
  - Promedio mensual y volatilidad

- **`indicadores_calculados`**: Indicadores derivados
  - `tasa_real`: Tasa de interés real (BADLAR - IPC)
  - `tcr`: Tipo de cambio real
  - `accesibilidad`: Índice de accesibilidad automotriz
  - `volatilidad`: Volatilidad macro agregada

---

## 🔄 Pipeline de Trabajo

### Script 1: `01_preparacion_datos_ml.py`

**Propósito**: Carga, unifica y prepara datos para ML

**Pasos**:
1. **Carga de datos transaccionales**
   - Unifica inscripciones, transferencias y prendas
   - Añade columna `tipo_transaccion` para identificar origen
   - Filtra desde 2020 en adelante

2. **Carga de variables macro**
   - Obtiene IPC, BADLAR, Tipo de Cambio, Indicadores calculados
   - Agrega a nivel mensual
   - Forward-fill para valores faltantes

3. **Agregación de transacciones**
   - Agrupa por: `fecha_mes`, `marca`, `modelo`, `provincia`, `tipo_transaccion`, `genero`
   - Calcula: cantidad de transacciones, edad promedio, año modelo promedio

4. **Feature Engineering**
   - Variables temporales: `trimestre`, `es_primer_semestre`, `es_fin_anio`
   - Lag features: valores del mes anterior (lag1) y hace 3 meses (lag3)
   - Rolling averages: MA3, MA6 (promedios móviles)
   - Variación intermensual de cantidad
   - Rangos de edad: '18-25', '26-35', '36-45', '46-55', '56-65', '65+'

5. **Guardado**
   - `dataset_ml_completo.parquet`: Dataset completo
   - `dataset_ml_sample.parquet`: Top 20 marcas (para desarrollo rápido)
   - `dataset_ml_metadata.csv`: Metadatos de columnas

**Ejecución**:
```bash
python notebooks/01_preparacion_datos_ml.py
```

**Outputs**:
- `data/processed/ml/dataset_ml_completo.parquet`
- `data/processed/ml/dataset_ml_sample.parquet`
- `data/processed/ml/dataset_ml_metadata.csv`

---

### Script 2: `02_modelado_predictivo.py`

**Propósito**: Entrenar y evaluar múltiples modelos de ML

**Pasos**:
1. **Carga de datos preparados**
   - Lee dataset de muestra o completo

2. **Identificación de tipos de columnas**
   - Numéricas: variables continuas
   - Categóricas alta cardinalidad: `marca`, `modelo` → **Label Encoding**
   - Categóricas baja cardinalidad: `provincia`, `genero`, `tipo_transaccion` → **One-Hot Encoding**

3. **Preparación de features**
   - Aplica Label Encoding para alta cardinalidad
   - Aplica One-Hot Encoding para baja cardinalidad
   - Imputa NaN con mediana (variables numéricas)
   - Genera vector de features final

4. **Split Train/Test**
   - 80% entrenamiento, 20% prueba
   - Random state 42 para reproducibilidad

5. **Entrenamiento de modelos** (con GridSearchCV)
   - Regresión Lineal (baseline)
   - Ridge Regression
   - Lasso Regression
   - Random Forest
   - XGBoost
   - LightGBM
   - KNN

6. **Evaluación**
   - Métricas: MAE, RMSE, R², MAPE
   - Comparación Train vs Test (detectar overfitting)
   - Ranking de modelos por R² Test

7. **Guardado**
   - Mejor modelo
   - Todos los modelos
   - Encoders
   - Feature names
   - Feature importance
   - Comparación de resultados

**Ejecución**:
```bash
python notebooks/02_modelado_predictivo.py
```

**Outputs**:
- `data/models/mejor_modelo_<nombre>.pkl`
- `data/models/todos_modelos_<timestamp>.pkl`
- `data/models/encoders.pkl`
- `data/models/feature_names.pkl`
- `data/results/comparacion_modelos_<timestamp>.csv`
- `data/results/feature_importance_<nombre>.csv`

---

### Script 3: `03_predicciones.py`

**Propósito**: Realizar predicciones con modelos entrenados

**Funcionalidades**:
1. **Predicción simple**: Para una combinación marca/modelo/provincia/mes
2. **Predicción múltiples escenarios**: Simula escenarios optimista/base/pesimista

**Escenarios definidos**:
- **Optimista**: IPC bajo, BADLAR moderada, TC estable
- **Base**: Condiciones actuales
- **Pesimista**: IPC alto, BADLAR alta, TC en alza

**Ejecución**:
```bash
python notebooks/03_predicciones.py
```

**Outputs**:
- `data/results/predicciones_escenarios_<timestamp>.csv`

---

## 🤖 Modelos Implementados

### 1. Regresión Lineal (Baseline)
- **Propósito**: Modelo simple para establecer benchmark
- **Ventajas**: Interpretable, rápido
- **Limitaciones**: Asume relaciones lineales

### 2. Ridge & Lasso Regression
- **Propósito**: Regularización para evitar overfitting
- **Ridge**: Penaliza L2 (magnitud de coeficientes)
- **Lasso**: Penaliza L1 (feature selection)

### 3. Random Forest Regressor
- **Propósito**: Ensemble de árboles de decisión
- **Ventajas**: No lineal, maneja interacciones, robusto
- **Hiperparámetros**: n_estimators, max_depth, min_samples_split

### 4. XGBoost
- **Propósito**: Gradient Boosting optimizado
- **Ventajas**: Alta performance, maneja missing values
- **Hiperparámetros**: learning_rate, max_depth, subsample

### 5. LightGBM
- **Propósito**: Gradient Boosting rápido y eficiente
- **Ventajas**: Rápido en datasets grandes, maneja categóricas
- **Hiperparámetros**: num_leaves, learning_rate, max_depth

### 6. KNN Regressor
- **Propósito**: Vecinos más cercanos
- **Ventajas**: No paramétrico, simple
- **Hiperparámetros**: n_neighbors, weights, metric

---

## 🚀 Ejecución

### Paso 1: Preparación de datos
```bash
cd /path/to/mercado_automotor
python notebooks/01_preparacion_datos_ml.py
```

**Duración estimada**: 5-15 minutos (según tamaño de datos)

### Paso 2: Entrenamiento de modelos
```bash
python notebooks/02_modelado_predictivo.py
```

**Duración estimada**: 15-30 minutos (con GridSearchCV)

**Para entrenamiento rápido** (sin GridSearch):
- Editar script y cambiar `usar_grid_search=False`

### Paso 3: Predicciones
```bash
python notebooks/03_predicciones.py
```

**Duración estimada**: < 1 minuto

---

## 📈 Resultados Esperados

### Métricas de Evaluación

| Métrica | Descripción | Interpretación |
|---------|-------------|----------------|
| **MAE** | Mean Absolute Error | Error promedio en cantidad de transacciones |
| **RMSE** | Root Mean Squared Error | Error penalizando grandes desviaciones |
| **R²** | Coeficiente de determinación | % de varianza explicada (0-1, ideal cercano a 1) |
| **MAPE** | Mean Absolute Percentage Error | Error porcentual promedio |

### Ejemplo de Resultados

```
================================================================================
Rank   Modelo               MAE Test     RMSE Test    R² Test      MAPE Test
================================================================================
1      LightGBM             245.32       412.18       0.8542       12.34%
2      XGBoost              258.19       428.65       0.8421       13.12%
3      Random_Forest        267.84       445.23       0.8298       14.05%
4      Ridge                312.45       502.18       0.7845       16.78%
5      Regresion_Lineal     318.92       515.34       0.7723       17.34%
6      Lasso                325.67       528.91       0.7612       18.01%
7      KNN                  389.23       612.45       0.6834       21.45%
================================================================================
```

### Feature Importance (Top 10)

Variables más importantes para predicción:
1. `cantidad_transacciones_lag1` - Valor mes anterior
2. `cantidad_ma3` - Promedio móvil 3 meses
3. `ipc_var_mensual` - Variación IPC
4. `badlar_promedio` - Tasa BADLAR
5. `marca_encoded` - Marca del vehículo
6. `mes` - Estacionalidad
7. `tc_promedio` - Tipo de cambio
8. `provincia_encoded` - Provincia
9. `tasa_real_promedio` - Tasa de interés real
10. `edad_titular` - Edad promedio compradores

---

## 🔮 Uso de Predicciones

### Ejemplo 1: Predicción para un mes específico

```python
from notebooks.predicciones import cargar_modelo_y_artefactos, preparar_datos_prediccion, predecir

# Cargar modelo
modelo, encoders, feature_names = cargar_modelo_y_artefactos()

# Preparar datos
df_pred = preparar_datos_prediccion(
    marca="TOYOTA",
    modelo_nombre="COROLLA",
    provincia="CAPITAL FEDERAL",
    tipo_transaccion="inscripcion",
    mes_prediccion=12,
    anio_prediccion=2024
)

# Predecir
prediccion = predecir(modelo, encoders, feature_names, df_pred)
print(f"Predicción: {prediccion:.0f} transacciones")
```

### Ejemplo 2: Análisis de sensibilidad macro

```python
# Escenario optimista (IPC bajo, economía estable)
df_pred['ipc_var_mensual'] = 3.0
df_pred['badlar_promedio'] = 45.0
prediccion_opt = predecir(modelo, encoders, feature_names, df_pred)

# Escenario pesimista (IPC alto, economía volátil)
df_pred['ipc_var_mensual'] = 8.0
df_pred['badlar_promedio'] = 65.0
prediccion_pes = predecir(modelo, encoders, feature_names, df_pred)

print(f"Diferencia: {prediccion_pes - prediccion_opt:.0f} transacciones")
```

---

## 📁 Estructura de Archivos Generados

```
mercado_automotor/
├── data/
│   ├── processed/
│   │   └── ml/
│   │       ├── dataset_ml_completo.parquet     # Dataset completo
│   │       ├── dataset_ml_sample.parquet       # Dataset muestra
│   │       └── dataset_ml_metadata.csv         # Metadatos
│   ├── models/
│   │   ├── mejor_modelo_LightGBM.pkl          # Mejor modelo
│   │   ├── todos_modelos_<timestamp>.pkl      # Todos los modelos
│   │   ├── encoders.pkl                       # Encoders categóricos
│   │   └── feature_names.pkl                  # Nombres de features
│   └── results/
│       ├── comparacion_modelos_<timestamp>.csv
│       ├── feature_importance_<modelo>.csv
│       └── predicciones_escenarios_<timestamp>.csv
└── notebooks/
    ├── 01_preparacion_datos_ml.py
    ├── 02_modelado_predictivo.py
    ├── 03_predicciones.py
    └── README_ML.md
```

---

## 🔧 Configuración y Dependencias

### Librerías Requeridas

```bash
pip install pandas numpy scikit-learn xgboost lightgbm
pip install sqlalchemy psycopg2-binary
pip install pyarrow  # para parquet
```

### Variables de Entorno

El script usa `backend.config.settings` que lee de `.env`:
```
DATABASE_URL=postgresql://user:password@host:port/mercado_automotor
```

---

## 💡 Tips y Mejores Prácticas

### Para Desarrollo Rápido
- Usar `dataset_ml_sample.parquet` (top 20 marcas)
- Desactivar GridSearchCV: `usar_grid_search=False`
- Reducir hiperparámetros a probar en `crear_modelos()`

### Para Producción
- Usar `dataset_ml_completo.parquet`
- Activar GridSearchCV con más iteraciones
- Considerar validación cruzada temporal (TimeSeriesSplit)

### Optimizaciones Futuras
1. **Feature Engineering avanzado**:
   - Interacciones entre variables macro
   - Tendencias de largo plazo
   - Componentes estacionales ARIMA

2. **Modelos adicionales**:
   - Prophet (Facebook) para series temporales
   - LSTM/GRU (Deep Learning)
   - Ensemble stacking de mejores modelos

3. **Validación robusta**:
   - Cross-validation temporal
   - Backtesting con ventanas deslizantes
   - Análisis de residuos

4. **Deployment**:
   - API REST para predicciones
   - Dashboard interactivo (Streamlit)
   - Re-entrenamiento automático mensual

---

## 📞 Soporte

Para preguntas o problemas:
1. Revisar logs de ejecución
2. Verificar que datos estén en PostgreSQL
3. Confirmar que `01_preparacion_datos_ml.py` completó exitosamente

---

**Autor**: Pipeline de ML - Mercado Automotor Argentino
**Última actualización**: 2024
