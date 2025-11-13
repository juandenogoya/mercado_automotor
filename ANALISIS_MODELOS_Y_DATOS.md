# 📊 Análisis de Modelos y Datos Disponibles - Mercado Automotor

**Fecha:** 2025-11-13
**Estado:** Post-implementación de datasets macroeconómicos

---

## 🎯 Resumen Ejecutivo

Hemos completado exitosamente la carga de **4,252 registros macroeconómicos** en PostgreSQL, transformando datos mensuales de IPC a frecuencia diaria. Ahora podemos avanzar con modelos analíticos y predictivos que antes no eran viables.

### Datasets Disponibles (Actualizado)

| Dataset | Registros | Período Estimado | Frecuencia | Estado |
|---------|-----------|------------------|------------|--------|
| **IPC Mensual** | 58 | ~5 años | Mensual | ✅ Operativo |
| **IPC Diario** | 1,765 | ~5 años | Diaria | ✅ **NUEVO** |
| **BADLAR** | 1,214 | ~3-4 años | Diaria (días hábiles) | ✅ Operativo |
| **Tipo de Cambio** | 1,215 | ~3-4 años | Diaria (días hábiles) | ✅ Operativo |
| Patentamientos | 0 | - | Mensual | ❌ Sin datos |
| Producción | 0 | - | Mensual | ❌ Sin datos |
| MercadoLibre | 0 | - | Diaria | ❌ Sin datos |
| BCRA Indicadores | 37 | Variable | Variable | ⚠️ Parcial |

**Total registros macro:** 4,252

---

## 📈 Análisis de Datos Macroeconómicos

### 1. IPC Diario (Inflación)

**Características:**
- **1,765 registros diarios** (resultado de expansión de 58 meses)
- Lógica aplicada: **Opción B (Vigencia)**
  - IPC medido en mes M → se aplica a TODO el mes M+1
  - Ejemplo: IPC Sept 2024 = 2.5% → aplicado a Oct 1-31, 2024
- Metadata completa: `periodo_medido` y `periodo_vigencia`

**Cobertura temporal:**
- ~58 meses de datos (desde 2020 aproximadamente)
- Permite análisis de tendencias de inflación
- Suficiente para modelos de forecasting

**Casos de uso:**
- ✅ Forecasting de inflación (1-3 meses adelante)
- ✅ Cálculo de inflación acumulada
- ✅ Análisis de correlación con otras variables macro
- ✅ Detección de picos inflacionarios

### 2. BADLAR (Tasa de Interés)

**Características:**
- **1,214 registros diarios**
- Tasa de interés en % TNA (Tasa Nominal Anual)
- Días hábiles bancarios (sin sábados/domingos/feriados)

**Cobertura temporal:**
- ~3-4 años de datos
- Alta frecuencia (diaria)

**Casos de uso:**
- ✅ Cálculo de tasa real (BADLAR - IPC)
- ✅ Forecasting de tasas de interés
- ✅ Análisis de política monetaria
- ✅ Indicador de costo de financiamiento para vehículos

### 3. Tipo de Cambio (USD/ARS)

**Características:**
- **1,215 registros diarios**
- Tipo de cambio BNA (Banco Nación Argentina)
- Incluye: promedio, compra, venta

**Cobertura temporal:**
- ~3-4 años de datos
- Días hábiles bancarios

**Casos de uso:**
- ✅ Cálculo de tipo de cambio real (TC / IPC acumulado)
- ✅ Análisis de devaluación
- ✅ Correlación con precios de vehículos importados
- ✅ Forecasting de tipo de cambio

---

## 🔍 Problemas Identificados con Modelos Anteriores

### ❌ Problema 1: Falta de Datos Sectoriales

**Estado anterior:**
- Patentamientos: 0 registros
- Producción: 0 registros
- MercadoLibre: 0 registros

**Impacto:**
Los indicadores específicos del sector automotor **NO son viables** actualmente:

1. ❌ **Índice de Tensión de Demanda**
   - Requiere: Patentamientos + BADLAR + IPC
   - Faltante: Patentamientos

2. ❌ **Rotación Estimada por Terminal**
   - Requiere: Producción + Patentamientos
   - Faltante: Ambos datasets

3. ❌ **Ranking de Atención de Marca**
   - Requiere: MercadoLibre + Google Trends
   - Faltante: Ambos datasets

### ❌ Problema 2: Frecuencia Mensual de IPC

**Estado anterior:**
- IPC solo disponible mensualmente (58 registros)
- Imposible correlacionar con datasets diarios (BADLAR, TC)
- Modelos de ML requieren alta frecuencia

**Solución implementada:**
- ✅ **IPC Diario creado** (1,765 registros)
- ✅ Metodología de vigencia aplicada
- ✅ Ahora compatible con BADLAR y TC para análisis integrado

### ❌ Problema 3: Datasets Sin Contexto Macro

**Estado anterior:**
- Solo datos macroeconómicos aislados
- Sin indicadores calculados/derivados
- Sin análisis de correlaciones

**Solución propuesta:**
- ✅ Crear nuevos indicadores derivados (ver sección siguiente)

---

## ✅ Nuevos Indicadores Viables (Con Datos Actuales)

### 1. Índice de Accesibilidad de Compra (NUEVO)

**Fórmula:**
```
Accesibilidad = (TC Real × BADLAR Real) / IPC Acumulado × 100
```

**Componentes:**
- IPC Diario: ✅ 1,765 registros
- BADLAR: ✅ 1,214 registros
- Tipo de Cambio: ✅ 1,215 registros

**Viabilidad:** 🟢 **ALTA**

**Interpretación:**
- Valores bajos → Menor capacidad de compra
- Valores altos → Mayor capacidad de compra
- Útil para: Ajustar precios, condiciones de financiamiento

**Próximo paso:**
Crear script `calcular_accesibilidad_compra.py` que:
1. Lee IPC Diario, BADLAR, TC del período común
2. Calcula IPC acumulado
3. Calcula tasa real = BADLAR - IPC
4. Calcula TC real = TC / IPC acumulado
5. Genera índice compuesto
6. Guarda en tabla `indicadores_calculados`

---

### 2. Índice de Costo de Financiamiento Real (NUEVO)

**Fórmula:**
```
Tasa Real = BADLAR (% TNA) - IPC (% mensual anualizado)
```

**Componentes:**
- BADLAR: ✅ 1,214 registros diarios
- IPC Diario: ✅ 1,765 registros diarios

**Viabilidad:** 🟢 **ALTA**

**Interpretación:**
- Tasa real positiva → Costo de financiamiento > inflación
- Tasa real negativa → Costo de financiamiento < inflación (subsidio implícito)
- Crucial para: Decisiones de financiamiento de clientes

**Ejemplo:**
```
BADLAR = 85% TNA
IPC = 6% mensual = 72% anual (aprox)
Tasa Real = 85% - 72% = +13% → Financiamiento caro
```

**Próximo paso:**
Crear indicador diario de tasa real y detectar períodos de "ventana de financiamiento barato"

---

### 3. Índice de Tipo de Cambio Real (NUEVO)

**Fórmula:**
```
TCR = TC Nominal / (IPC / IPC Base)
```

**Componentes:**
- Tipo de Cambio: ✅ 1,215 registros
- IPC Diario: ✅ 1,765 registros

**Viabilidad:** 🟢 **ALTA**

**Interpretación:**
- TCR subiendo → Dólar se apreció en términos reales
- TCR cayendo → Dólar se depreció (atraso cambiario)
- Útil para: Precios de vehículos importados

**Próximo paso:**
Calcular TCR histórico y detectar ciclos de atraso/ajuste cambiario

---

### 4. Volatilidad Macro (NUEVO)

**Fórmula:**
```
Volatilidad = σ(IPC) + σ(BADLAR) + σ(TC)
```
Donde σ = desviación estándar móvil (30 días)

**Componentes:**
- IPC Diario: ✅ 1,765 registros
- BADLAR: ✅ 1,214 registros
- Tipo de Cambio: ✅ 1,215 registros

**Viabilidad:** 🟢 **ALTA**

**Interpretación:**
- Alta volatilidad → Incertidumbre macro, clientes postergan compras
- Baja volatilidad → Estabilidad, mejora demanda

**Próximo paso:**
Crear índice de volatilidad macro diario

---

## 🤖 Modelos de ML Viables (Con Datos Actuales)

### Modelo 1: Forecasting de IPC (Prophet / ARIMA)

**Objetivo:**
Predecir inflación 1-3 meses adelante

**Datos:**
- ✅ IPC Diario: 1,765 registros (~58 meses)
- ✅ Suficiente para Prophet (requiere mín. 6-12 meses)

**Metodología:**
```python
# Prophet (Facebook)
from prophet import Prophet

model = Prophet(
    seasonality_mode='multiplicative',
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False
)

model.fit(df[['ds', 'y']])  # ds = fecha, y = ipc_mensual
forecast = model.predict(future_dates)  # 1-3 meses adelante
```

**Viabilidad:** 🟢 **ALTA**

**Métricas esperadas:**
- MAE (Mean Absolute Error) < 2 puntos porcentuales
- R² > 0.80

**Valor comercial:**
- Anticipar períodos de alta inflación
- Ajustar precios proactivamente
- Planificar promociones

**Próximo paso:**
Implementar `forecast_ipc.py` con Prophet

---

### Modelo 2: Forecasting de BADLAR (ARIMA)

**Objetivo:**
Predecir tasas de interés 7-30 días adelante

**Datos:**
- ✅ BADLAR: 1,214 registros diarios

**Metodología:**
```python
from statsmodels.tsa.arima.model import ARIMA

# Auto-ARIMA para encontrar mejor (p,d,q)
model = ARIMA(badlar_ts, order=(5,1,2))
model_fit = model.fit()
forecast = model_fit.forecast(steps=30)
```

**Viabilidad:** 🟢 **ALTA**

**Valor comercial:**
- Anticipar cambios en costo de financiamiento
- Ajustar tasa de planes de ahorro/prendario

**Próximo paso:**
Implementar `forecast_badlar.py` con ARIMA

---

### Modelo 3: Análisis de Correlación Macro (VAR)

**Objetivo:**
Identificar relaciones entre IPC, BADLAR, TC

**Datos:**
- ✅ Período común de ~3-4 años con los 3 datasets

**Metodología:**
```python
from statsmodels.tsa.api import VAR

# Vector Autoregression
model = VAR(df[['ipc', 'badlar', 'tc']])
results = model.fit(maxlags=15)

# Impulse Response Functions
irf = results.irf(10)
irf.plot()  # Ver cómo un shock en IPC afecta BADLAR y TC
```

**Viabilidad:** 🟢 **ALTA**

**Insights esperados:**
- ¿Un shock en TC causa aumento de IPC? (pass-through)
- ¿BADLAR reacciona a cambios en IPC? (política monetaria)
- ¿TC y BADLAR están correlacionados?

**Próximo paso:**
Crear `analisis_correlacion_macro.py`

---

### Modelo 4: Detección de Anomalías (Isolation Forest)

**Objetivo:**
Detectar eventos atípicos en datos macro

**Datos:**
- ✅ IPC, BADLAR, TC diarios

**Metodología:**
```python
from sklearn.ensemble import IsolationForest

clf = IsolationForest(contamination=0.05)
anomalies = clf.fit_predict(df[['ipc', 'badlar', 'tc']])
```

**Viabilidad:** 🟡 **MEDIA**

**Casos de uso:**
- Detectar "eventos de mercado" (devaluaciones, saltos de tasa)
- Generar alertas automáticas

**Próximo paso:**
Implementar sistema de alertas

---

### Modelo 5: Clustering de Regímenes Macro (K-Means)

**Objetivo:**
Identificar períodos de "alta inflación / baja tasa" vs "baja inflación / alta tasa"

**Datos:**
- ✅ Features: IPC, BADLAR, TC, volatilidad

**Metodología:**
```python
from sklearn.cluster import KMeans

kmeans = KMeans(n_clusters=3)  # 3 regímenes
df['regime'] = kmeans.fit_predict(df[features])

# Regímenes esperados:
# 0 = Crisis (alta inflación, alto TC, alta tasa)
# 1 = Estabilidad (baja inflación, TC estable)
# 2 = Transición
```

**Viabilidad:** 🟡 **MEDIA**

**Valor comercial:**
- Adaptar estrategia comercial según régimen
- En crisis → Promociones agresivas, financiamiento flexible
- En estabilidad → Precios normales, menos descuentos

**Próximo paso:**
Crear `clustering_regimenes.py`

---

## 🚀 Plan de Acción Recomendado

### CORTO PLAZO (Esta Semana)

1. **✅ COMPLETADO:** Cargar datos macro (IPC, BADLAR, TC)
2. **🔨 IMPLEMENTAR:** Calcular indicadores derivados
   - Script: `calcular_indicadores_macro.py`
   - Indicadores: Tasa Real, TCR, Accesibilidad, Volatilidad
   - Guardar en tabla `indicadores_calculados`

3. **🔨 IMPLEMENTAR:** Análisis exploratorio de correlaciones
   - Script: `analisis_correlacion_macro.py`
   - Gráficos: Matriz de correlaciones, scatter plots
   - Export: PDF con análisis

### MEDIANO PLAZO (Próximas 2 Semanas)

4. **🔨 IMPLEMENTAR:** Forecasting de IPC (Prophet)
   - Script: `forecast_ipc.py`
   - Predicción: 1-3 meses adelante
   - Visualización: Gráfico con intervalos de confianza

5. **🔨 IMPLEMENTAR:** Forecasting de BADLAR (ARIMA)
   - Script: `forecast_badlar.py`
   - Predicción: 7-30 días adelante

6. **📊 DASHBOARD:** Agregar página de "Indicadores Macro"
   - Streamlit dashboard con:
     - Gráficos de IPC, BADLAR, TC
     - Indicadores calculados
     - Forecasts

### LARGO PLAZO (Próximo Mes)

7. **📁 CARGAR DATOS SECTORIALES:**
   - Patentamientos (ACARA scraper)
   - Producción (ADEFA scraper)
   - MercadoLibre precios (API)

8. **🔨 IMPLEMENTAR:** Indicadores sectoriales
   - Tensión de demanda (requiere patentamientos)
   - Rotación de stock (requiere producción)

9. **🤖 ML AVANZADO:**
   - Modelo de predicción de demanda
   - Clustering de vehículos por segmento
   - Recomendador de precios

---

## 📊 Estructura de Código Propuesta

```
backend/
├── scripts/
│   ├── calcular_indicadores_macro.py  # NUEVO
│   ├── analisis_correlacion_macro.py  # NUEVO
│   ├── forecast_ipc.py                # NUEVO
│   ├── forecast_badlar.py             # NUEVO
│   └── clustering_regimenes.py        # NUEVO
│
├── models/
│   └── indicadores_calculados.py      # YA EXISTE
│
└── analytics/  # NUEVO DIRECTORIO
    ├── __init__.py
    ├── forecasting.py      # Funciones reutilizables
    ├── indicators.py       # Cálculos de indicadores
    └── correlations.py     # Análisis de correlaciones
```

---

## 💡 Conclusiones

### ✅ Lo que SÍ podemos hacer ahora:

1. **Análisis macro completo** con IPC, BADLAR, TC
2. **Forecasting de inflación** (Prophet)
3. **Forecasting de tasas** (ARIMA)
4. **Indicadores derivados** (tasa real, TCR, accesibilidad)
5. **Análisis de correlaciones** (VAR, matrices)
6. **Detección de anomalías** (eventos de mercado)

### ❌ Lo que NO podemos hacer todavía:

1. Indicadores específicos del sector automotor
2. Análisis de demanda/oferta de vehículos
3. Precios de mercado de vehículos
4. Rankings de marcas/modelos

### 🎯 Prioridad Inmediata:

**Implementar los 4 indicadores macro nuevos** (Accesibilidad, Tasa Real, TCR, Volatilidad) para demostrar valor inmediato con los datos que ya tenemos.

**Luego:** Forecasting de IPC con Prophet para tener predicciones accionables.

---

**Siguiente paso sugerido:** ¿Quieres que implemente el script `calcular_indicadores_macro.py` que cree los 4 nuevos indicadores derivados?
