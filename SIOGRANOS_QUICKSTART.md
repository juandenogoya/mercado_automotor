# 🌾 SIOGRANOS ETL - Inicio Rápido

## ¿Qué es esto?

Sistema ETL para cargar **5 años de datos de operaciones de granos** (2020-2025) desde la API SIOGRANOS a PostgreSQL.

**Objetivo**: Correlacionar precio/volumen de granos (especialmente **soja**) con ventas de **pick-ups** y vehículos rurales.

---

## 🚀 Instalación en 5 minutos

### Opción A: Script Automático (Recomendado)

```bash
# 1. Ejecutar script de setup
bash setup_siogranos.sh

# 2. Editar .env con tu contraseña de PostgreSQL
nano .env

# 3. Re-ejecutar setup
bash setup_siogranos.sh

# 4. Lanzar ETL
python etl_siogranos.py
```

### Opción B: Manual

```bash
# 1. Instalar dependencias
pip install requests psycopg2-binary python-dotenv tabulate

# 2. Crear .env
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mercado_automotor
DB_USER=postgres
DB_PASSWORD=tu_password
SIOGRANOS_API_URL=https://test.bc.org.ar/SiogranosAPI/api/ConsultaPublica/consultarOperaciones
EOF

# 3. Crear base de datos
createdb mercado_automotor

# 4. Crear tablas
psql -d mercado_automotor -f database/schemas/siogranos_schema.sql

# 5. Ejecutar ETL
python etl_siogranos.py
```

---

## 📊 Uso

### Carga inicial (histórico completo)

```bash
python etl_siogranos.py
```

**Resultado**:
- ✅ ~296 chunks procesados (7 días cada uno)
- ✅ ~850k operaciones cargadas
- ⏱️ Tiempo: 15-30 minutos

### Ver progreso

```bash
# En otra terminal
python verificar_chunks_siogranos.py
```

### Reanudar carga interrumpida

```bash
# Simplemente volver a ejecutar
python etl_siogranos.py
```

El script automáticamente:
- ✅ Omite chunks ya completados
- ✅ Retoma desde el último pendiente
- ✅ No duplica datos

---

## 🗂️ Archivos creados

```
mercado_automotor/
├── database/schemas/
│   └── siogranos_schema.sql          # Schema PostgreSQL
│
├── etl_siogranos.py                  # Script ETL principal
├── verificar_chunks_siogranos.py     # Verificación de progreso
├── siogranos_codigos.py              # Códigos de granos/provincias
├── test_siogranos_api.py             # Test de API
│
├── setup_siogranos.sh                # Setup automático
├── etl_siogranos.log                 # Logs de ejecución
│
├── docs/
│   └── ETL_SIOGRANOS.md              # Documentación completa
│
└── .env                              # Configuración (crear)
```

---

## 📈 Consultas útiles

### Precio promedio soja por mes (últimos 24 meses)

```sql
SELECT
    DATE_TRUNC('month', fecha_operacion) AS mes,
    AVG(precio_tn) AS precio_promedio_soja_usd,
    SUM(volumen_tn) AS volumen_total_tn
FROM siogranos_operaciones
WHERE nombre_grano = 'SOJA'
  AND simbolo_moneda = 'USD'
  AND fecha_operacion >= CURRENT_DATE - INTERVAL '24 months'
GROUP BY DATE_TRUNC('month', fecha_operacion)
ORDER BY mes DESC;
```

### Provincias con mayor actividad agrícola

```sql
SELECT * FROM v_siogranos_resumen_provincial
WHERE mes >= '2024-01-01'
ORDER BY volumen_total_tn DESC
LIMIT 10;
```

### Índice de liquidez agropecuaria por provincia

```sql
SELECT * FROM v_siogranos_indice_liquidez
WHERE mes >= '2023-01-01'
ORDER BY liquidez_millones DESC;
```

---

## 🔍 Verificar datos cargados

```sql
-- Estadísticas generales
SELECT
    COUNT(*) AS total_registros,
    MIN(fecha_operacion) AS fecha_min,
    MAX(fecha_operacion) AS fecha_max,
    COUNT(DISTINCT nombre_grano) AS total_granos,
    COUNT(DISTINCT nombre_provincia_procedencia) AS total_provincias,
    SUM(volumen_tn) AS volumen_total_tn
FROM siogranos_operaciones;

-- Resumen por grano
SELECT
    nombre_grano,
    COUNT(*) AS operaciones,
    SUM(volumen_tn) AS volumen_total_tn,
    AVG(precio_tn) AS precio_promedio_tn
FROM siogranos_operaciones
GROUP BY nombre_grano
ORDER BY volumen_total_tn DESC;
```

---

## ⚠️ Troubleshooting

### "Connection refused to PostgreSQL"

```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Iniciar si está detenido
sudo systemctl start postgresql
```

### "API timeout" frecuente

Editar `etl_siogranos.py`:

```python
# Aumentar timeout
REQUEST_TIMEOUT = 120  # De 60s a 120s

# Reducir tamaño de chunk
CHUNK_DAYS = 3  # De 7 a 3 días
```

### Servidor de testing sin datos

Si `https://test.bc.org.ar/...` devuelve 0 operaciones:

1. Obtener URL de **producción** de SIOGRANOS
2. Actualizar `.env`:
   ```
   SIOGRANOS_API_URL=https://api.bc.org.ar/SiogranosAPI/...
   ```

---

## 📚 Documentación completa

Ver: **[docs/ETL_SIOGRANOS.md](docs/ETL_SIOGRANOS.md)**

---

## 🎯 Próximos pasos

Una vez cargados los datos:

1. **Análisis exploratorio** en Jupyter:
   ```bash
   jupyter notebook notebooks/analisis_siogranos.ipynb
   ```

2. **Correlación con datos automotor**:
   - Cruzar precio soja con ventas pick-ups
   - Identificar delay temporal (3-6 meses)
   - Crear modelo predictivo

3. **Dashboard en tiempo real**:
   - Streamlit con métricas clave
   - Alertas cuando precio soja sube/baja
   - Predicción de demanda pick-ups

---

## 💡 ¿Por qué es útil?

### Correlación directa

```
Precio Soja ↑ → Liquidez Rural ↑ → Compra Pick-ups ↑
(con delay de 3-6 meses)
```

### Segmentación geográfica

- **Buenos Aires**: 40% del volumen de granos
- **Santa Fe**: 25%
- **Córdoba**: 20%

→ Focos de ventas de pick-ups

### Timing de campañas

- **Post-cosecha gruesa** (soja): Abril-Julio
- **Post-cosecha fina** (trigo): Diciembre-Enero

→ Momentos óptimos para promociones

---

**Última actualización**: 2025-11-10
