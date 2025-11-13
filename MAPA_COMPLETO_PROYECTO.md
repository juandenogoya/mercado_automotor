# 🗺️ Mapa Completo del Proyecto - Mercado Automotor

**Fecha de Generación:** 2025-11-13 20:41:20
**Proyecto:** Sistema de Inteligencia Comercial para el Sector Automotor Argentino

---

## 📋 Índice

1. Resumen Ejecutivo
2. Inventario de Ramas
3. Detalles Completos por Rama
4. Próximos Pasos Recomendados

---

## 🎯 Resumen Ejecutivo

### Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Total de Ramas** | 7 |
| **Total de Modelos (sum)** | 22 |
| **Total de Scripts (sum)** | 16 |
| **Total de Documentos (sum)** | 15 |
| **Fecha de Análisis** | 2025-11-13 20:41:20 |

### Objetivos del Proyecto

- **Sistema de Inteligencia Comercial** para gerencias comerciales del sector automotor
- **Integración de fuentes públicas**: ACARA, ADEFA, BCRA, INDEC, MercadoLibre, datos.gob.ar
- **Análisis predictivo** con ML para anticipar tendencias de mercado
- **Dashboard interactivo** para visualización y exploración de datos
- **Indicadores macro** para medir accesibilidad, volatilidad, tasas reales

---

## 🌿 Inventario de Ramas

El proyecto tiene **7** ramas de desarrollo:

| Rama | Modelos | Scripts | Docs | Último Commit | Objetivo Inferido |
|------|---------|---------|------|---------------|-------------------|
| `claude/continue-project-011CUzjS5wAvCY8xCtvfzV16` | 6 | 0 | 5 | 2025-11-13 | Continuación del proyecto. Dashboard interactivo datos.gob.ar con análisis YoY y MoM. Entrenamiento de modelos ML. |
| `claude/dashboard-analisis-detallado-011CUzjS5wAvCY8xCtvfzV16` | 0 | 0 | 0 | N/A | Dashboard de análisis detallado. |
| `claude/fix-siogranos-period-query-011CUzR82FowxLdziTxxppKn` | 0 | 0 | 0 | N/A | Corrección de bugs y problemas técnicos. |
| `claude/review-project-advantages-011CUvWjZ32MibKBCTEhtWn8` | 6 | 1 | 5 | 2025-11-10 | Exploración de ventajas competitivas. Integración de datos.gob.ar DNRPA (13.6M registros: Inscripciones, Transferencias, Prendas). |
| `claude/review-project-summary-011CV66WdV3iGNxtg8RMd2ZN` | 10 | 15 | 5 | 2025-11-13 | Revisión y resumen del proyecto. Cálculo de indicadores macroeconómicos (IPC, BADLAR, TC). |
| `claude/sync-dashboard-detallado-011CUzjS5wAvCY8xCtvfzV16` | 0 | 0 | 0 | N/A | Dashboard de análisis detallado. |
| `desarrollo/dashboard-datos-gob-2025` | 0 | 0 | 0 | N/A | Rama principal de desarrollo. Dashboard datos.gob.ar 2025. |


---

## 📚 Detalles Completos por Rama


### 🌿 Rama: `claude/continue-project-011CUzjS5wAvCY8xCtvfzV16`

**Último Commit:**
- Hash: `d40cb413`
- Autor: Claude
- Fecha: 2025-11-13 14:41:55 +0000
- Mensaje: feat: Script para analizar contenido del parquet de forecasting

**Objetivo:**
Continuación del proyecto. Dashboard interactivo datos.gob.ar con análisis YoY y MoM. Entrenamiento de modelos ML.

**Modelos Definidos (6):**
- `BCRAIndicador`
- `Base`
- `IndicadorCalculado`
- `MercadoLibreListing`
- `Patentamiento`
- `Produccion`

**Documentación (5):**
- `DASHBOARD_DATOS_GOB.md`
- `FUENTES_DATOS_INVESTIGACION.md`
- `README.md`
- `RESUMEN_PROYECTO.md`
- `RESUMEN_SESION.md`

---

### 🌿 Rama: `claude/dashboard-analisis-detallado-011CUzjS5wAvCY8xCtvfzV16`

**Objetivo:**
Dashboard de análisis detallado.

---

### 🌿 Rama: `claude/fix-siogranos-period-query-011CUzR82FowxLdziTxxppKn`

**Objetivo:**
Corrección de bugs y problemas técnicos.

---

### 🌿 Rama: `claude/review-project-advantages-011CUvWjZ32MibKBCTEhtWn8`

**Último Commit:**
- Hash: `2a94c986`
- Autor: Claude
- Fecha: 2025-11-10 16:49:21 +0000
- Mensaje: fix: Corregir ESTADO_PROYECTO.md enfocándolo en datos.gob.ar

**Objetivo:**
Exploración de ventajas competitivas. Integración de datos.gob.ar DNRPA (13.6M registros: Inscripciones, Transferencias, Prendas).

**Modelos Definidos (6):**
- `BCRAIndicador`
- `Base`
- `IndicadorCalculado`
- `MercadoLibreListing`
- `Patentamiento`
- `Produccion`

**Scripts Disponibles (1):**
- `explore_indec_series.py`

**Documentación (5):**
- `DNRPA_SCRAPER.md`
- `ESTADO_PROYECTO.md`
- `FUENTES_DATOS_INVESTIGACION.md`
- `README.md`
- `RESUMEN_PROYECTO.md`

---

### 🌿 Rama: `claude/review-project-summary-011CV66WdV3iGNxtg8RMd2ZN`

**Último Commit:**
- Hash: `31b13b44`
- Autor: Claude
- Fecha: 2025-11-13 20:29:13 +0000
- Mensaje: feat: agregar script explorador de BCRA automotores (WIP)

**Objetivo:**
Revisión y resumen del proyecto. Cálculo de indicadores macroeconómicos (IPC, BADLAR, TC).

**Modelos Definidos (10):**
- `BADLAR`
- `BCRAIndicador`
- `Base`
- `IPC`
- `IPCDiario`
- `IndicadorCalculado`
- `MercadoLibreListing`
- `Patentamiento`
- `Produccion`
- `TipoCambio`

**Scripts Disponibles (15):**
- `analisis_simple_db.py`
- `analizar_datos_disponibles.py`
- `analizar_series_ipc.py`
- `calcular_indicadores_macro.py`
- `calcular_variaciones_ipc.py`
- `cargar_datos_macro.py`
- `diagnosticar_ipc.py`
- `expandir_ipc_diario.py`
- `explorar_bcra_automotores.py`
- `generar_diccionario_datos.py`
- `recargar_ipc_diario.py`
- `test_bcra_api.py`
- `test_bcra_simple.py`
- `test_bcra_v4.py`
- `test_indec_ids.py`

**Documentación (5):**
- `ANALISIS_MODELOS_Y_DATOS.md`
- `FUENTES_DATOS_INVESTIGACION.md`
- `INDICADORES_CALCULADOS.md`
- `README.md`
- `RESUMEN_PROYECTO.md`

---

### 🌿 Rama: `claude/sync-dashboard-detallado-011CUzjS5wAvCY8xCtvfzV16`

**Objetivo:**
Dashboard de análisis detallado.

---

### 🌿 Rama: `desarrollo/dashboard-datos-gob-2025`

**Objetivo:**
Rama principal de desarrollo. Dashboard datos.gob.ar 2025.

---


## 🚀 Próximos Pasos Recomendados

### Para Comenzar una Nueva Sesión

1. **Revisar este documento** (`MAPA_COMPLETO_PROYECTO.md`) para entender el estado actual
2. **Verificar el Excel** (`INVENTARIO_DATASETS_COMPLETO.xlsx`) para conocer datasets disponibles
3. **Consultar rama específica** según el objetivo:
   - Para indicadores macro → `claude/review-project-summary-*`
   - Para datos.gob.ar dashboard → `claude/continue-project-*`
   - Para datos DNRPA completos (13.6M) → `claude/review-project-advantages-*`

### Comandos Útiles para Cambiar de Rama

```bash
# Ver todas las ramas
git branch -a

# Cambiar a una rama específica
git checkout <nombre-rama>

# Crear rama local tracking desde remote
git checkout -b <nombre-rama> origin/<nombre-rama>

# Ver diferencias entre ramas
git diff <rama1>..<rama2>
```

### Tareas Pendientes Identificadas

- [ ] Unificar datasets de todas las ramas en una sola
- [ ] Integrar modelos de datos.gob.ar (Inscripciones, Transferencias, Prendas)
- [ ] Completar carga de datos históricos
- [ ] Entrenar y validar modelos de ML
- [ ] Desarrollar dashboard unificado

---

## 📞 Información Adicional

**Stack Tecnológico:**
- Python 3.11+
- PostgreSQL 15 + TimescaleDB
- FastAPI (API REST)
- Streamlit (Dashboards)
- SQLAlchemy (ORM)
- Pandas, NumPy (Análisis)
- Scikit-learn, XGBoost, Prophet (ML)

**Fuentes de Datos Integradas:**
- ACARA (patentamientos)
- ADEFA (producción)
- BCRA (tasas, indicadores económicos)
- INDEC (IPC, inflación)
- MercadoLibre (precios de mercado)
- datos.gob.ar - DNRPA (inscripciones, transferencias, prendas)

---

**Generado automáticamente por:** `backend/scripts/analizar_todas_ramas_standalone.py`
**Fecha:** {current_date}
