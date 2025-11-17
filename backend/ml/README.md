# 🤖 Modelo de Propensión de Compra - Machine Learning

## 📋 Descripción General

Este módulo implementa un **sistema de Machine Learning** para predecir la **propensión de compra por marca** de vehículos, basándose en características demográficas, geográficas y KPIs del mercado automotor.

El modelo responde preguntas como:
- *"Un hombre de 35 años de La Plata, ¿qué marca tiene más probabilidad de comprar?"*
- *"Para mujeres de 25-34 años en Córdoba, ¿cuáles son las top 5 marcas más probables?"*
- *"¿Qué marcas tienen mayor propensión en el segmento de personas jurídicas?"*

## 🎯 Características del Modelo

### **Features Utilizadas**

El modelo utiliza más de 20 features derivadas de los KPIs materializados:

#### 1. **Demográficas**
- Provincia y localidad del titular
- Rango de edad (18-24, 25-34, 35-44, 45-54, 55-64, 65+)
- Género (M, F, OTRO)
- Tipo de persona (FÍSICA, JURÍDICA)

#### 2. **Características del Vehículo**
- Tipo de vehículo (AUTOMÓVIL, MOTOVEHÍCULO, etc.)
- Origen (NACIONAL, IMPORTADO)

#### 3. **KPIs de Mercado**
- **IF (Índice de Financiamiento)**: Propensión a financiar compras
- **EVT (Edad del Vehículo al Transferirse)**: Antigüedad en mercado de usados
- **IAM (Índice de Antigüedad del Mercado)**: Antigüedad del parque automotor
- **IDA (Índice de Demanda Activa)**: Relación transferencias/inscripciones

#### 4. **Features Derivadas**
- **Tasa de crecimiento mensual**: Variación de inscripciones vs mes anterior
- **Tasa de crecimiento YoY**: Variación vs mismo mes año anterior
- **Concentración de marca**: Participación de marca en localidad
- **Ranking de marca**: Posición de marca en localidad
- **Estacionalidad**: Componentes sinusoidales del mes (mes_sin, mes_cos)
- **Ratios**: Prendas/Inscripciones, Transferencias/Inscripciones
- **Flags**: Es marca top-5, Alta concentración (>30%)
- **Segmento de mercado**: Nuevos (<3 años), Seminuevos (3-7), Usados (>7)

### **Algoritmos Soportados**

1. **Random Forest** (default)
   - Robusto a overfitting
   - Maneja bien features categóricas
   - Proporciona feature importance

2. **XGBoost** (opcional)
   - Mayor precisión en datasets grandes
   - Optimización avanzada con gradient boosting

3. **LightGBM** (opcional)
   - Más rápido que XGBoost
   - Eficiente en memoria

### **Métricas de Evaluación**

- **Accuracy**: Precisión general del modelo
- **Precision/Recall/F1-Score**: Por clase (marca)
- **Top-3 Accuracy**: % de veces que la marca correcta está en top-3
- **Top-5 Accuracy**: % de veces que la marca correcta está en top-5
- **Feature Importance**: Ranking de features más influyentes

## 🚀 Instalación y Configuración

### **Requisitos**

```bash
# Instalar dependencias
pip install -r requirements.txt

# Dependencias principales:
# - pandas >= 1.5.0
# - numpy >= 1.23.0
# - scikit-learn >= 1.3.0
# - xgboost >= 2.0.0 (opcional)
# - lightgbm >= 4.0.0 (opcional)
# - sqlalchemy >= 2.0.0
```

### **Preparación de KPIs**

El modelo requiere que los KPIs estén materializados en PostgreSQL:

```bash
# 1. Inicializar KPIs materializados
python backend/scripts/actualizar_kpis.py --inicializar

# 2. Verificar estadísticas
python backend/scripts/actualizar_kpis.py --stats
```

## 📊 Uso del Sistema

### **1. Preparar Datos**

Extrae features desde PostgreSQL y realiza feature engineering:

```bash
# RECOMENDADO: Usar TODOS los años disponibles (omitir --anios)
python backend/ml/preparar_datos_propension.py --output data/ml/

# Alternativamente, especificar años concretos
python backend/ml/preparar_datos_propension.py --anios 2020,2021,2022,2023,2024 --output data/ml/

# Opciones:
#   --anios: Años a incluir (ej: 2020,2021,2022,2023,2024). Si se omite, usa TODOS los años (RECOMENDADO)
#   --min-inscripciones: Mínimo de inscripciones para incluir registro (default: 10)
#   --output: Directorio de salida (default: data/ml/propension_compra/)
#   --test-size: % de test set (default: 0.2)
```

**💡 Recomendación:** Omite el parámetro `--anios` para usar todos los años disponibles en la base de datos.
**Beneficios de usar más años:**
- ✅ Mayor precisión y generalización del modelo
- ✅ Captura tendencias de largo plazo y ciclos económicos
- ✅ Detecta patrones estacionales multianuales
- ✅ Reduce overfitting al tener más ejemplos de entrenamiento

**Salida:**
```
data/ml/propension_compra/
├── X_train.npy              # Features de entrenamiento
├── X_test.npy               # Features de test
├── y_train.npy              # Target de entrenamiento
├── y_test.npy               # Target de test
├── encoders.pkl             # Label encoders para categóricas
├── feature_names.pkl        # Nombres de features
├── preparacion_metadata.json # Metadata del proceso
└── reporte_eda.txt          # Análisis exploratorio
```

### **2. Entrenar Modelo**

Entrena modelos de ML y selecciona el mejor:

```bash
# Entrenar todos los modelos (RF, XGBoost, LightGBM)
python backend/ml/entrenar_modelo_propension.py --input data/ml/propension_compra/

# Solo Random Forest (más rápido)
python backend/ml/entrenar_modelo_propension.py --input data/ml/ --only-rf

# Personalizar parámetros
python backend/ml/entrenar_modelo_propension.py \
    --input data/ml/ \
    --n-estimators 200 \
    --max-depth 25 \
    --output data/ml/modelos/
```

**Opciones:**
- `--input`: Directorio con datos preparados
- `--output`: Directorio para guardar modelos (default: data/ml/modelos/)
- `--n-estimators`: Número de árboles en Random Forest (default: 100)
- `--max-depth`: Profundidad máxima de árboles (default: 20)
- `--only-rf`: Entrenar solo Random Forest (más rápido)

**Salida:**
```
data/ml/modelos/
├── modelo_propension_compra.pkl    # Mejor modelo entrenado
├── encoders.pkl                    # Encoders para predicción
├── feature_names.pkl               # Nombres de features
├── feature_importance.csv          # Importancia de features
├── modelo_metadata.json            # Metadata y métricas
└── reporte_entrenamiento.txt       # Reporte detallado
```

### **3. Realizar Predicciones**

#### **3.1 Predicción Individual**

```bash
python backend/ml/predecir_propension.py \
    --provincia "BUENOS AIRES" \
    --localidad "LA PLATA" \
    --edad 35 \
    --genero M \
    --tipo-persona FISICA \
    --tipo-vehiculo AUTOMOVIL \
    --origen NACIONAL \
    --top 5
```

**Salida:**
```
📊 Top 5 Marcas con Mayor Propensión:
============================================================
   1. TOYOTA              28.45% ██████████████
   2. VOLKSWAGEN          22.18% ███████████
   3. FIAT                18.32% █████████
   4. CHEVROLET           15.67% ███████
   5. RENAULT             11.23% █████
============================================================
```

#### **3.2 Predicción en Batch**

Procesa múltiples perfiles desde un CSV:

```bash
# Preparar CSV con perfiles
# Columnas: provincia, localidad, edad, genero, tipo_persona, tipo_vehiculo, origen

python backend/ml/predecir_propension.py \
    --batch \
    --input perfiles_usuarios.csv \
    --output resultados_predicciones.csv \
    --top 5
```

**CSV de entrada (perfiles_usuarios.csv):**
```csv
provincia,localidad,edad,genero,tipo_persona,tipo_vehiculo,origen
BUENOS AIRES,LA PLATA,35,M,FISICA,AUTOMOVIL,NACIONAL
CORDOBA,CORDOBA,28,F,FISICA,AUTOMOVIL,IMPORTADO
SANTA FE,ROSARIO,45,M,JURIDICA,CAMION,NACIONAL
```

**CSV de salida (resultados_predicciones.csv):**
```csv
provincia,localidad,edad,genero,...,marca_top_1,probabilidad_top_1,marca_top_2,probabilidad_top_2,...
BUENOS AIRES,LA PLATA,35,M,...,TOYOTA,28.45,VOLKSWAGEN,22.18,...
CORDOBA,CORDOBA,28,F,...,FIAT,32.11,RENAULT,24.56,...
SANTA FE,ROSARIO,45,M,...,MERCEDES-BENZ,35.67,IVECO,28.34,...
```

#### **3.3 Predicción desde Dashboard**

El modelo está integrado en **TAB 8: KPIs de Mercado** del dashboard Streamlit:

```bash
# Iniciar dashboard
streamlit run frontend/app_datos_gob.py
```

1. Ir a **TAB 8: KPIs de Mercado**
2. Scroll hasta **🔮 Predicción de Propensión de Compra (ML)**
3. Completar formulario con perfil del usuario
4. Presionar **"Predecir Propensión"**
5. Ver resultados: gráfico de barras, tabla y métricas

## 📈 Interpretación de Resultados

### **Feature Importance**

Después de entrenar, revisa `feature_importance.csv` para entender qué features son más influyentes:

```csv
feature,importance
edad_promedio_comprador,0.18
provincia,0.15
indice_financiamiento,0.12
concentracion_marca_localidad,0.11
evt_promedio,0.09
...
```

### **Métricas del Modelo**

Revisa `modelo_metadata.json` para ver el rendimiento:

```json
{
  "accuracy": 0.72,
  "f1_score": 0.68,
  "top_3_accuracy": 0.89,
  "top_5_accuracy": 0.94,
  "training_time": 45.32,
  "n_classes": 47,
  "n_samples": 125340
}
```

**Interpretación:**
- **Accuracy (72%)**: El modelo acierta la marca exacta en 72% de casos
- **Top-3 Accuracy (89%)**: La marca correcta está en el top-3 en 89% de casos
- **Top-5 Accuracy (94%)**: La marca correcta está en el top-5 en 94% de casos

Esto significa que el modelo es **muy útil para recomendaciones** (top-N), incluso si la predicción exacta no es perfecta.

## 🔄 Flujo de Trabajo Completo

### **Workflow Típico**

```bash
# 1. Cargar datos nuevos en PostgreSQL
python backend/scripts/cargar_estadisticas_agregadas.py --archivo nuevos_datos.csv

# 2. Actualizar KPIs materializados
python backend/scripts/actualizar_kpis.py --refresh --concurrent

# 3. Re-preparar datos con datos actualizados (usar todos los años disponibles)
python backend/ml/preparar_datos_propension.py --output data/ml/

# 4. Re-entrenar modelo
python backend/ml/entrenar_modelo_propension.py --input data/ml/

# 5. Usar en predicciones
python backend/ml/predecir_propension.py --provincia "CABA" --localidad "PALERMO" --edad 30 --genero F
```

### **Automatización con Cron**

```bash
# Actualizar modelo semanalmente (domingos a las 3 AM)
0 3 * * 0 cd /ruta/proyecto && \
    python backend/scripts/actualizar_kpis.py --refresh --concurrent && \
    python backend/ml/preparar_datos_propension.py --output data/ml/ && \
    python backend/ml/entrenar_modelo_propension.py --input data/ml/ --only-rf \
    >> logs/ml_update.log 2>&1
```

## 🧪 Ejemplos de Uso

### **Ejemplo 1: Recomendación para Usuario Específico**

```python
from backend.ml.predecir_propension import predecir_propension_compra

resultados = predecir_propension_compra(
    provincia="BUENOS AIRES",
    localidad="LA PLATA",
    edad=35,
    genero="M",
    tipo_persona="FISICA",
    tipo_vehiculo="AUTOMOVIL",
    origen="NACIONAL",
    top_n=5
)

for i, (marca, probabilidad) in enumerate(resultados, 1):
    print(f"{i}. {marca}: {probabilidad*100:.2f}%")
```

### **Ejemplo 2: Análisis de Segmentos**

```python
import pandas as pd
from backend.ml.predecir_propension import predecir_propension_compra

# Analizar diferentes segmentos de edad
segmentos = [
    {"edad": 25, "label": "18-34"},
    {"edad": 40, "label": "35-54"},
    {"edad": 65, "label": "55+"}
]

for seg in segmentos:
    resultados = predecir_propension_compra(
        provincia="CABA",
        localidad="PALERMO",
        edad=seg["edad"],
        genero="M",
        top_n=3
    )
    print(f"\nSegmento {seg['label']}:")
    for marca, prob in resultados[:3]:
        print(f"  {marca}: {prob*100:.1f}%")
```

### **Ejemplo 3: A/B Testing de Campañas**

```python
# Comparar propensión entre diferentes localidades
localidades = ["LA PLATA", "MAR DEL PLATA", "BAHIA BLANCA"]

for loc in localidades:
    resultados = predecir_propension_compra(
        provincia="BUENOS AIRES",
        localidad=loc,
        edad=30,
        genero="F",
        top_n=1
    )
    marca_top, prob_top = resultados[0]
    print(f"{loc}: {marca_top} ({prob_top*100:.1f}%)")
```

## 🔧 Mantenimiento y Optimización

### **Re-entrenamiento Periódico**

El modelo debe re-entrenarse cuando:
- Hay datos nuevos significativos (ej: cada mes/trimestre)
- Cambian tendencias del mercado
- El rendimiento baja en producción

### **Monitoreo del Modelo**

```python
# Verificar feature importance periódicamente
import pandas as pd

fi = pd.read_csv("data/ml/modelos/feature_importance.csv")
print("Top 10 features más importantes:")
print(fi.head(10))

# Si features irrelevantes tienen mucha importancia, re-evaluar feature engineering
```

### **Tuning de Hiperparámetros**

Para mejorar el rendimiento:

```python
# Usar GridSearchCV para encontrar mejores parámetros
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [15, 20, 25, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=5,
    scoring='f1_weighted',
    n_jobs=-1
)

grid_search.fit(X_train, y_train)
print(f"Mejores parámetros: {grid_search.best_params_}")
```

## 📊 Casos de Uso

### **1. Marketing Segmentado**

Identificar marcas con mayor propensión para cada segmento demográfico:

```bash
# Segmento: Mujeres jóvenes de CABA
python backend/ml/predecir_propension.py \
    --provincia "CABA" --localidad "PALERMO" \
    --edad 28 --genero F --top 5
```

### **2. Planificación de Inventario**

Distribuidores pueden anticipar demanda por localidad:

```python
# Predecir top marcas para múltiples localidades
localidades_zona_sur = ["LA PLATA", "QUILMES", "LOMAS DE ZAMORA"]

for loc in localidades_zona_sur:
    resultados = predecir_propension_compra(
        provincia="BUENOS AIRES",
        localidad=loc,
        edad=35,
        genero="M",
        top_n=3
    )
    # Usar resultados para planificar stock
```

### **3. Recomendaciones en Plataformas**

Integrar en sitios web de concesionarias:

```python
# API endpoint para recomendaciones
@app.route('/api/recomendar-marcas', methods=['POST'])
def recomendar_marcas():
    data = request.json

    resultados = predecir_propension_compra(
        provincia=data['provincia'],
        localidad=data['localidad'],
        edad=data['edad'],
        genero=data['genero'],
        top_n=5
    )

    return jsonify({
        'marcas': [
            {'marca': m, 'probabilidad': p*100}
            for m, p in resultados
        ]
    })
```

## 🐛 Troubleshooting

### **Error: "Modelo no encontrado"**

```bash
# Verificar que el modelo fue entrenado
ls -l data/ml/modelos/modelo_propension_compra.pkl

# Si no existe, entrenar (usar todos los años disponibles):
python backend/ml/preparar_datos_propension.py --output data/ml/
python backend/ml/entrenar_modelo_propension.py --input data/ml/
```

### **Error: "Feature X no encontrada"**

Asegúrate de que los KPIs estén actualizados:

```bash
python backend/scripts/actualizar_kpis.py --stats
python backend/scripts/actualizar_kpis.py --refresh
```

### **Predicciones poco precisas**

1. Verificar que hay datos suficientes:
```bash
python backend/scripts/actualizar_kpis.py --stats
```

2. Re-entrenar con todos los años disponibles:
```bash
# Usar todos los años disponibles (RECOMENDADO)
python backend/ml/preparar_datos_propension.py --output data/ml/
python backend/ml/entrenar_modelo_propension.py --input data/ml/
```

3. Aumentar complejidad del modelo:
```bash
python backend/ml/entrenar_modelo_propension.py \
    --n-estimators 300 \
    --max-depth 30
```

## 📚 Referencias

- **Scikit-learn**: https://scikit-learn.org/
- **XGBoost**: https://xgboost.readthedocs.io/
- **LightGBM**: https://lightgbm.readthedocs.io/
- **Feature Engineering**: https://www.kaggle.com/learn/feature-engineering

## 👥 Soporte

Para problemas o preguntas:
1. Revisar logs: `logs/ml_update.log`
2. Verificar metadata: `data/ml/modelos/modelo_metadata.json`
3. Consultar feature importance: `data/ml/modelos/feature_importance.csv`
4. Revisar documentación de KPIs: `backend/sql/README_KPIS.md`

## 📝 Notas Importantes

1. **Performance**: El modelo Random Forest con 100 árboles tarda ~30-60 segundos en entrenar
2. **Memoria**: XGBoost y LightGBM requieren más memoria (~2-4 GB para datasets grandes)
3. **Predicción**: Las predicciones individuales son muy rápidas (~10-50ms)
4. **Actualización**: Re-entrenar mensualmente o cuando haya cambios significativos en datos
5. **Interpretabilidad**: Random Forest proporciona mejor interpretabilidad que deep learning
