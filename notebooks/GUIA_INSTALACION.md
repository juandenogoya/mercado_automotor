# 🚀 Guía de Instalación y Ejecución - Pipeline ML

Guía paso a paso para ejecutar el pipeline de Machine Learning del proyecto Mercado Automotor.

---

## 📍 Información de la Rama

**Rama actual**: `claude/review-project-summary-011CV66WdV3iGNxtg8RMd2ZN`

Todos los scripts de ML están en esta rama.

---

## ✅ Pre-requisitos

Antes de comenzar, verifica que tengas:

1. ✅ **Python 3.8+** instalado
   ```powershell
   python --version
   # Debe mostrar: Python 3.8.x o superior
   ```

2. ✅ **PostgreSQL** con los datos cargados
   - Tablas: `datos_gob_inscripciones`, `datos_gob_transferencias`, `datos_gob_prendas`
   - Tablas: `ipc`, `badlar`, `tipo_cambio`, `indicadores_calculados`

3. ✅ **Archivo `.env`** con credenciales de base de datos
   ```
   DATABASE_URL=postgresql://usuario:password@host:puerto/mercado_automotor
   ```

---

## 📦 PASO 1: Obtener el Código

### En tu PC (Windows PowerShell):

```powershell
# Navegar al directorio del proyecto
cd C:\Users\juand\OneDrive\Escritorio\concecionaria\mercado_automotor

# Obtener los últimos cambios
git pull origin claude/review-project-summary-011CV66WdV3iGNxtg8RMd2ZN

# Verificar que estás en la rama correcta
git branch --show-current
# Debe mostrar: claude/review-project-summary-011CV66WdV3iGNxtg8RMd2ZN

# Verificar que los archivos están presentes
dir notebooks\
# Debes ver: 01_preparacion_datos_ml.py, 02_modelado_predictivo.py, 03_predicciones.py
```

---

## 🐍 PASO 2: Crear Entorno Virtual (RECOMENDADO)

**¿Por qué usar entorno virtual?**
- Aisla las dependencias del proyecto
- Evita conflictos con otros proyectos Python
- Facilita la gestión de versiones

### Opción A: Crear nuevo entorno virtual

```powershell
# Crear entorno virtual llamado 'venv_ml'
python -m venv venv_ml

# Activar el entorno virtual
.\venv_ml\Scripts\activate

# Debes ver (venv_ml) al inicio del prompt:
# (venv_ml) PS C:\Users\juand\OneDrive\Escritorio\concecionaria\mercado_automotor>
```

### Opción B: Usar entorno virtual existente

Si ya tienes un entorno virtual del proyecto:

```powershell
# Activar entorno existente
.\venv\Scripts\activate
```

---

## 📚 PASO 3: Instalar Dependencias

Con el entorno virtual activado:

```powershell
# Instalar dependencias de ML
pip install -r requirements_ml.txt

# Esto instalará:
# - pandas, numpy
# - scikit-learn
# - xgboost, lightgbm
# - sqlalchemy, psycopg2-binary
# - pyarrow (para Parquet)
```

**Verificar instalación:**

```powershell
# Verificar que las librerías se instalaron correctamente
python -c "import pandas, sklearn, xgboost, lightgbm; print('✓ Todas las librerías instaladas')"
```

---

## 🗂️ PASO 4: Verificar Estructura de Directorios

El pipeline creará automáticamente las carpetas necesarias, pero puedes verificar:

```powershell
# Crear directorios si no existen (opcional)
mkdir -Force data\processed\ml
mkdir -Force data\models
mkdir -Force data\results
```

---

## ▶️ PASO 5: Ejecutar el Pipeline

### 5.1 Preparación de Datos (15-30 min)

Este script carga datos de PostgreSQL, los procesa y genera el dataset de ML.

```powershell
# Ejecutar script de preparación
python notebooks\01_preparacion_datos_ml.py
```

**Qué hace:**
- ✅ Conecta a PostgreSQL
- ✅ Carga inscripciones, transferencias, prendas
- ✅ Carga variables macro (IPC, BADLAR, TC)
- ✅ Feature engineering (lag features, rolling averages)
- ✅ Guarda archivos Parquet en `data/processed/ml/`

**Outputs esperados:**
```
data/processed/ml/
├── dataset_ml_completo.parquet    # Dataset completo
├── dataset_ml_sample.parquet      # Top 20 marcas (para pruebas rápidas)
└── dataset_ml_metadata.csv        # Metadatos
```

**Logs clave a buscar:**
```
✓ Dataset unificado: XXX,XXX registros
✓ Variables macro unificadas: XX meses, XX variables
✓ Features creados: XX columnas totales
✅ PREPARACIÓN COMPLETADA
```

---

### 5.2 Entrenamiento de Modelos (20-45 min)

Este script entrena 7 modelos de ML con optimización de hiperparámetros.

```powershell
# Ejecutar entrenamiento
python notebooks\02_modelado_predictivo.py
```

**Qué hace:**
- ✅ Carga dataset preparado
- ✅ Aplica Label Encoding y One-Hot Encoding
- ✅ Entrena 7 modelos con GridSearchCV
- ✅ Evalúa con MAE, RMSE, R², MAPE
- ✅ Guarda mejor modelo y resultados

**Outputs esperados:**
```
data/models/
├── mejor_modelo_LightGBM.pkl      # Mejor modelo (ejemplo)
├── todos_modelos_<timestamp>.pkl  # Todos los modelos
├── encoders.pkl                   # Encoders de variables categóricas
└── feature_names.pkl              # Nombres de features

data/results/
├── comparacion_modelos_<timestamp>.csv
└── feature_importance_<modelo>.csv
```

**Logs clave a buscar:**
```
🏆 COMPARACIÓN DE MODELOS
Rank   Modelo          MAE Test    R² Test
1      LightGBM        245.32      0.8542
2      XGBoost         258.19      0.8421
...

🥇 MEJOR MODELO: LightGBM
   R² Test: 0.8542
✅ MODELADO COMPLETADO
```

---

### 5.3 Predicciones (< 1 min)

Este script usa el modelo entrenado para hacer predicciones.

```powershell
# Ejecutar predicciones
python notebooks\03_predicciones.py
```

**Qué hace:**
- ✅ Carga mejor modelo entrenado
- ✅ Hace predicción de ejemplo (Toyota Corolla)
- ✅ Analiza múltiples escenarios (optimista/base/pesimista)
- ✅ Guarda resultados

**Outputs esperados:**
```
data/results/
└── predicciones_escenarios_<timestamp>.csv
```

---

## 🔍 PASO 6: Revisar Resultados

### 6.1 Comparación de Modelos

```powershell
# Ver resultados de modelos
type data\results\comparacion_modelos_*.csv
```

### 6.2 Feature Importance

```powershell
# Ver qué variables son más importantes
type data\results\feature_importance_*.csv
```

### 6.3 Predicciones de Escenarios

```powershell
# Ver predicciones bajo diferentes condiciones económicas
type data\results\predicciones_escenarios_*.csv
```

---

## ⚙️ CONFIGURACIÓN AVANZADA

### Opción 1: Usar Dataset Completo (Producción)

Por defecto, el script usa `dataset_ml_sample.parquet` (top 20 marcas) para rapidez.

Para usar todos los datos:

```python
# Editar: notebooks/02_modelado_predictivo.py
# Línea ~60, cambiar:

# DE:
file_path = INPUT_DIR / "dataset_ml_sample.parquet"

# A:
file_path = INPUT_DIR / "dataset_ml_completo.parquet"
```

### Opción 2: Desactivar GridSearchCV (Entrenamiento Rápido)

Para entrenar más rápido sin optimización:

```python
# Editar: notebooks/02_modelado_predictivo.py
# Línea ~430, cambiar:

# DE:
resultados, modelos_entrenados = entrenar_y_evaluar(
    X_train, X_test, y_train, y_test, modelos, usar_grid_search=True
)

# A:
resultados, modelos_entrenados = entrenar_y_evaluar(
    X_train, X_test, y_train, y_test, modelos, usar_grid_search=False
)
```

### Opción 3: Entrenar Solo Algunos Modelos

Para entrenar solo modelos específicos:

```python
# Editar: notebooks/02_modelado_predictivo.py
# En la función crear_modelos(), comentar los que no quieras:

modelos = {
    'Regresion_Lineal': {...},  # Mantener
    # 'Ridge': {...},           # Comentar
    # 'Lasso': {...},           # Comentar
    'Random_Forest': {...},     # Mantener
    'XGBoost': {...},           # Mantener
    # 'LightGBM': {...},        # Comentar
    # 'KNN': {...}              # Comentar
}
```

---

## 🐛 Solución de Problemas

### Error: "No module named 'xgboost'"

```powershell
pip install xgboost lightgbm
```

### Error: "Can't connect to PostgreSQL"

Verifica tu archivo `.env`:
```powershell
type .env
# Debe tener: DATABASE_URL=postgresql://...
```

### Error: "No se encuentra dataset_ml_sample.parquet"

Ejecuta primero el script de preparación:
```powershell
python notebooks\01_preparacion_datos_ml.py
```

### Advertencia: "SettingWithCopyWarning"

Es normal, son advertencias de pandas. Los scripts funcionan correctamente.

### Error de memoria (MemoryError)

Si el dataset es muy grande:
1. Usa `dataset_ml_sample.parquet` en lugar del completo
2. Reduce el período de análisis (editar filtro `>= '2020-01-01'`)
3. Aumenta RAM disponible o cierra otros programas

---

## 📊 Tiempos Estimados

| Script | Duración Estimada | Observaciones |
|--------|-------------------|---------------|
| 01_preparacion | 10-20 min | Depende de cantidad de datos en PostgreSQL |
| 02_modelado (con GridSearch) | 30-45 min | 7 modelos × múltiples hiperparámetros |
| 02_modelado (sin GridSearch) | 5-10 min | Más rápido, parámetros por defecto |
| 03_predicciones | < 1 min | Muy rápido |

---

## 🔄 Flujo Completo Resumido

```powershell
# 1. Preparar entorno
git pull
python -m venv venv_ml
.\venv_ml\Scripts\activate
pip install -r requirements_ml.txt

# 2. Ejecutar pipeline
python notebooks\01_preparacion_datos_ml.py    # ~15 min
python notebooks\02_modelado_predictivo.py     # ~30 min
python notebooks\03_predicciones.py            # < 1 min

# 3. Revisar resultados
dir data\results\
type data\results\comparacion_modelos_*.csv
```

---

## 📞 Checklist Pre-Ejecución

Antes de ejecutar, verifica:

- [ ] Estoy en la rama correcta (`claude/review-project-summary-011CV66WdV3iGNxtg8RMd2ZN`)
- [ ] Tengo Python 3.8+ instalado
- [ ] PostgreSQL tiene los datos cargados
- [ ] Archivo `.env` existe con DATABASE_URL correcta
- [ ] Entorno virtual está activado
- [ ] Dependencias instaladas (`pip install -r requirements_ml.txt`)
- [ ] Tengo ~2GB de espacio en disco para outputs

---

## 📁 Archivos que se Generarán

Después de ejecutar todo, tendrás:

```
mercado_automotor/
├── data/
│   ├── processed/ml/
│   │   ├── dataset_ml_completo.parquet      (~100-500 MB)
│   │   ├── dataset_ml_sample.parquet        (~20-50 MB)
│   │   └── dataset_ml_metadata.csv          (< 1 MB)
│   ├── models/
│   │   ├── mejor_modelo_LightGBM.pkl        (~10-50 MB)
│   │   ├── todos_modelos_<timestamp>.pkl    (~50-200 MB)
│   │   ├── encoders.pkl                     (< 1 MB)
│   │   └── feature_names.pkl                (< 1 MB)
│   └── results/
│       ├── comparacion_modelos_*.csv        (< 1 MB)
│       ├── feature_importance_*.csv         (< 1 MB)
│       └── predicciones_escenarios_*.csv    (< 1 MB)
└── notebooks/
    └── ... (scripts de Python)
```

**Espacio total requerido**: ~500 MB - 1 GB

---

## 🎯 Próximos Pasos Después de Ejecutar

1. **Revisar modelo ganador**:
   - Abrir `comparacion_modelos_*.csv`
   - Identificar modelo con mejor R² Test

2. **Analizar feature importance**:
   - Abrir `feature_importance_*.csv`
   - Identificar variables más predictivas

3. **Interpretar predicciones**:
   - Abrir `predicciones_escenarios_*.csv`
   - Comparar escenarios optimista vs pesimista

4. **Opcional - Integrar al dashboard**:
   - Agregar predicciones al Streamlit
   - Crear visualizaciones interactivas

---

**¿Listo para empezar?** 🚀

Empieza con: `python notebooks\01_preparacion_datos_ml.py`
