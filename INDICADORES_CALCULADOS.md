# 🧮 Indicadores Macroeconómicos Calculados

**Sistema de Cálculo Automático de Indicadores Derivados**

---

## 📊 Indicadores Disponibles

### 1. 💸 Tasa Real (Costo de Financiamiento Real)

**Fórmula:**
```
Tasa Real = BADLAR (% TNA) - IPC Anualizado (%)
```

**Interpretación:**
- **Tasa Real > 0**: El costo de financiamiento es mayor que la inflación → Financiamiento CARO
- **Tasa Real < 0**: El costo de financiamiento es menor que la inflación → Financiamiento BARATO (subsidio implícito)
- **Tasa Real ≈ 0**: Costo neutro

**Ejemplo:**
```
BADLAR = 85% TNA
IPC Mensual = 6% → IPC Anualizado ≈ 72%
Tasa Real = 85% - 72% = +13%
→ El financiamiento es 13 puntos más caro que la inflación
```

**Uso comercial:**
- **Alta tasa real**: Clientes evitan financiamiento, prefieren compras contado
- **Baja/negativa tasa real**: "Ventana" para promover planes de financiamiento agresivos

---

### 2. 💵 Tipo de Cambio Real (TCR)

**Fórmula:**
```
TCR = TC Nominal (ARS/USD) / (IPC Acumulado / 100)
```

**Interpretación:**
- **TCR subiendo**: Dólar se aprecia en términos reales → Devaluación efectiva
- **TCR cayendo**: Dólar se deprecia en términos reales → Atraso cambiario
- **TCR estable**: Tipo de cambio acompañando la inflación

**Uso comercial:**
- **TCR alto**: Vehículos importados más caros, favorecer nacionales
- **TCR bajo**: Vehículos importados competitivos, oportunidad de venta
- **Ciclos de TCR**: Detectar períodos de ajuste cambiario (devaluaciones esperables)

---

### 3. 💰 Índice de Accesibilidad de Compra

**Fórmula:**
```
Accesibilidad = (TCR × (100 + Tasa Real)) / IPC Acumulado × 100
Normalizado a base 100 en el primer día
```

**Interpretación:**
- **Índice > 100**: Mayor accesibilidad que período base
- **Índice < 100**: Menor accesibilidad que período base
- **Índice cayendo**: Deterioro del poder adquisitivo

**Componentes:**
- TCR: Refleja precio de vehículos (muchos importados o con componentes importados)
- Tasa Real: Refleja costo de financiamiento
- IPC Acumulado: Refleja erosión del poder adquisitivo

**Uso comercial:**
- **Accesibilidad alta (>110)**: Momento favorable para ventas, clientes pueden comprar
- **Accesibilidad baja (<90)**: Mercado difícil, ajustar expectativas, promociones agresivas
- **Tendencia**: Anticipar si el mercado mejorará o empeorará

---

### 4. 📈 Volatilidad Macro

**Fórmula:**
```
Volatilidad = Promedio de desviaciones estándar móviles (30 días) de:
  - IPC Diario
  - BADLAR
  - Tipo de Cambio
Normalizado y expresado como % compuesto
```

**Interpretación:**
- **Volatilidad alta (>5%)**: Incertidumbre macro, clientes postergan compras
- **Volatilidad baja (<2%)**: Estabilidad, mejora propensión a comprar
- **Spikes**: Eventos de mercado (devaluaciones, saltos de tasa)

**Uso comercial:**
- **Alta volatilidad**: Comunicación frecuente, precios flexibles, promociones cortas
- **Baja volatilidad**: Campañas de largo plazo, precios estables
- **Detectar shocks**: Prepararse para ajustes de precio después de eventos

---

## 🚀 Uso del Sistema

### Cálculo Inicial (Primera Vez)

```bash
# Calcular todos los indicadores desde el período común
python manage.py calcular-indicadores --export-excel indicadores_macro.xlsx
```

**Resultado:**
- ~1,200+ registros por indicador (según período común)
- 4 indicadores × ~1,200 días = ~4,800 registros totales
- Excel con 5 hojas (Resumen + 4 indicadores)

---

### Actualización Incremental

```bash
# Calcular solo desde una fecha específica (nuevos datos)
python manage.py calcular-indicadores --fecha-desde 2024-11-01
```

**Resultado:**
- Solo calcula indicadores para fechas >= 2024-11-01
- Actualiza registros existentes si hay cambios
- Inserta registros nuevos

---

### Recálculo Completo (Limpiar y Calcular)

```bash
# Limpiar indicadores anteriores y recalcular todo
python manage.py calcular-indicadores --limpiar --export-excel indicadores_macro.xlsx
```

**Resultado:**
- Elimina todos los indicadores anteriores
- Recalcula desde el inicio del período común
- Útil si cambiaron las fórmulas o hay correcciones en datos fuente

---

### Solo Exportar a Excel (Sin Calcular)

```bash
# Ejecutar script directamente para calcular y exportar
python backend/scripts/calcular_indicadores_macro.py --export-excel indicadores_macro.xlsx
```

---

## 📊 Verificar Resultados

### Ver Estadísticas en Base de Datos

```bash
python manage.py stats
```

**Output esperado:**
```
📊 Estadísticas de la base de datos:
  - Patentamientos: 0 registros
  - Producción: 0 registros
  - BCRA Indicadores: 37 registros
  - MercadoLibre Listings: 0 registros
  - IPC (mensual): 58 registros
  - IPC Diario: 1,765 registros
  - BADLAR: 1,214 registros
  - Tipo de Cambio: 1,215 registros
  - Indicadores Calculados: 4,856 registros

📈 Indicadores Calculados (desglose):
  - tasa_real: 1,214 registros
  - tipo_cambio_real: 1,214 registros
  - accesibilidad_compra: 1,214 registros
  - volatilidad_macro: 1,214 registros
```

---

### Consultar en PostgreSQL

```sql
-- Ver últimos 10 días de todos los indicadores
SELECT
    fecha,
    indicador,
    valor,
    unidad
FROM indicadores_calculados
WHERE fecha >= CURRENT_DATE - INTERVAL '10 days'
ORDER BY fecha DESC, indicador;

-- Tasa real promedio del último mes
SELECT
    AVG(valor) as tasa_real_promedio
FROM indicadores_calculados
WHERE indicador = 'tasa_real'
  AND fecha >= CURRENT_DATE - INTERVAL '30 days';

-- Detectar períodos de alta volatilidad
SELECT
    fecha,
    valor as volatilidad
FROM indicadores_calculados
WHERE indicador = 'volatilidad_macro'
  AND valor > 5.0
ORDER BY fecha DESC;

-- Evolución del TCR (últimos 6 meses)
SELECT
    fecha,
    valor as tcr
FROM indicadores_calculados
WHERE indicador = 'tipo_cambio_real'
  AND fecha >= CURRENT_DATE - INTERVAL '6 months'
ORDER BY fecha;
```

---

## 📈 Excel Generado

### Estructura del Archivo

**Hoja 1: Resumen**
- Vista general de los 4 indicadores
- Estadísticas: Min, Max, Promedio, Último valor
- Período de cobertura

**Hoja 2: Tasa Real**
- Fecha | Tasa Real (%) | BADLAR (%) | IPC Mensual (%)
- Permite ver la composición del indicador

**Hoja 3: TCR**
- Fecha | TCR | TC Nominal | IPC Mensual (%)
- Ver evolución del tipo de cambio real

**Hoja 4: Accesibilidad**
- Fecha | Índice Accesibilidad
- Índice base 100, fácil de graficar

**Hoja 5: Volatilidad**
- Fecha | Volatilidad (%)
- Detectar períodos de incertidumbre

### Análisis Sugeridos en Excel

1. **Gráfico de Tasa Real vs BADLAR vs IPC**
   - Eje Y izquierdo: Tasa Real
   - Eje Y derecho: BADLAR e IPC
   - Ver cómo la brecha cambia en el tiempo

2. **Gráfico de Línea: TCR**
   - Detectar ciclos de atraso/ajuste cambiario
   - Marcar devaluaciones importantes

3. **Gráfico de Área: Volatilidad**
   - Sombrear períodos de alta incertidumbre
   - Correlacionar con eventos macroeconómicos

4. **Gráfico Combinado: Accesibilidad vs Volatilidad**
   - ¿Cuando la volatilidad sube, la accesibilidad cae?
   - Identificar relación entre variables

---

## 🔄 Automatización

### Workflow Recomendado

```bash
# 1. Actualizar datos fuente (diario/semanal)
python manage.py cargar-macro --tipo all

# 2. Expandir IPC a diario (si hay nuevos meses)
python manage.py expandir-ipc-diario

# 3. Calcular indicadores nuevos
python manage.py calcular-indicadores --fecha-desde $(date -d "7 days ago" +%Y-%m-%d)

# 4. Ver estadísticas
python manage.py stats
```

### Airflow DAG (Futuro)

```python
# dag_indicadores_macro.py
from airflow import DAG
from datetime import datetime, timedelta

with DAG(
    'calcular_indicadores_macro',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:

    task_cargar_macro = BashOperator(
        task_id='cargar_macro',
        bash_command='python manage.py cargar-macro --tipo all'
    )

    task_expandir_ipc = BashOperator(
        task_id='expandir_ipc',
        bash_command='python manage.py expandir-ipc-diario'
    )

    task_calcular_indicadores = BashOperator(
        task_id='calcular_indicadores',
        bash_command='python manage.py calcular-indicadores --fecha-desde {{ ds }}'
    )

    task_cargar_macro >> task_expandir_ipc >> task_calcular_indicadores
```

---

## 📊 Casos de Uso Comerciales

### 1. Decisión de Financiamiento

```
Pregunta: ¿Debemos promover financiamiento este mes?

Consulta:
SELECT valor as tasa_real
FROM indicadores_calculados
WHERE indicador = 'tasa_real'
  AND fecha = CURRENT_DATE;

Regla:
- Tasa Real < 5%   → Promocionar financiamiento agresivamente
- Tasa Real 5-15%  → Financiamiento estándar
- Tasa Real > 15%  → Enfocarse en ventas contado, menos financiamiento
```

### 2. Ajuste de Precios de Importados

```
Pregunta: ¿El dólar está caro o barato en términos reales?

Consulta:
SELECT valor as tcr, fecha
FROM indicadores_calculados
WHERE indicador = 'tipo_cambio_real'
ORDER BY fecha DESC
LIMIT 30;

Análisis:
- Comparar TCR actual vs promedio 6 meses
- Si TCR > promedio + 10% → Dólar caro, subir precios importados
- Si TCR < promedio - 10% → Dólar barato, oportunidad de venta
```

### 3. Timing de Campañas

```
Pregunta: ¿Es buen momento para lanzar campaña?

Consulta:
SELECT
    a.valor as accesibilidad,
    v.valor as volatilidad
FROM indicadores_calculados a
JOIN indicadores_calculados v ON a.fecha = v.fecha
WHERE a.indicador = 'accesibilidad_compra'
  AND v.indicador = 'volatilidad_macro'
  AND a.fecha >= CURRENT_DATE - INTERVAL '7 days';

Regla:
- Accesibilidad > 100 AND Volatilidad < 3% → MOMENTO IDEAL
- Accesibilidad < 90 OR Volatilidad > 5%   → ESPERAR
```

### 4. Alerta de Riesgo Macro

```
Pregunta: ¿Hay señales de shock macroeconómico inminente?

Consulta:
SELECT fecha, valor
FROM indicadores_calculados
WHERE indicador = 'volatilidad_macro'
  AND valor > 5.0
  AND fecha >= CURRENT_DATE - INTERVAL '7 days';

Acción:
- Si hay spike de volatilidad → Preparar ajuste de precios
- Comunicar a equipo comercial
- Revisar stock de importados
```

---

## 🛠️ Mantenimiento

### Recalcular Si Cambian Datos Fuente

```bash
# Si se corrigen datos de IPC, BADLAR o TC
python manage.py calcular-indicadores --limpiar
```

### Verificar Integridad

```sql
-- Verificar que todos los indicadores tengan la misma cantidad de registros
SELECT indicador, COUNT(*) as registros
FROM indicadores_calculados
GROUP BY indicador;

-- Debe retornar 4 filas con el mismo número de registros
```

### Logs

Los logs del cálculo se guardan en:
- Console output (stdout)
- Loguru logs (si configurado)

---

## 📚 Referencias

**Fórmulas económicas:**
- Tasa Real: Fisher Equation
- Tipo de Cambio Real: IPC-based real exchange rate
- Volatilidad: Rolling standard deviation

**Datos fuente:**
- IPC: INDEC (mensual, expandido a diario)
- BADLAR: BCRA API v4.0 (diario)
- Tipo de Cambio: BCRA API v4.0 (diario)

---

## 🎯 Próximos Pasos

1. ✅ **Implementado**: Cálculo de 4 indicadores macro
2. 🔜 **Próximo**: Dashboard Streamlit para visualizar indicadores
3. 🔜 **Próximo**: Alertas automáticas cuando indicadores cruzan umbrales
4. 🔜 **Futuro**: Forecasting de indicadores (predecir tasa real, TCR)
5. 🔜 **Futuro**: Integrar con datos sectoriales (patentamientos) cuando estén disponibles

---

**Última actualización:** 2025-11-13
**Versión:** 1.0.0
