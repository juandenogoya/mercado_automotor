# 📊 Instrucciones: Estadísticas Agregadas Mensuales

## ¿Qué son estos datos?

Los archivos CSV de estadísticas agregadas contienen **totales mensuales por provincia** desde 2007:

| **Datos Detallados (PostgreSQL actual)** | **Datos Agregados (nuevos)** |
|------------------------------------------|------------------------------|
| 1 fila = 1 trámite individual | 1 fila = total mes/provincia |
| 13.6M registros, 4.92 GB | ~18K registros, 0.84 MB |
| Incluye marca, modelo, edad, etc. | Solo cantidad por mes/provincia |
| Desde 2019 | Desde 2007 |
| Solo autos/motos | Incluye **Maquinarias** |

---

## 🚀 Paso 1: Crear las Tablas en PostgreSQL

Abre PowerShell y ejecuta:

```powershell
cd C:\Users\juand\OneDrive\Escritorio\Concecionaria\mercado_automotor

# Ejecutar script SQL para crear las tablas
psql -h localhost -U postgres -d mercado_automotor -f sql/crear_tablas_estadisticas_agregadas.sql
```

Esto creará:
- ✅ Tabla `estadisticas_inscripciones`
- ✅ Tabla `estadisticas_transferencias`
- ✅ Índices para consultas rápidas
- ✅ Vistas para análisis (totales nacionales, rankings provinciales)

---

## 📥 Paso 2: Cargar los Datos CSV

```powershell
# Cargar los 4 archivos CSV a PostgreSQL
python cargar_estadisticas_agregadas.py
```

**¿Qué hace este script?**
- 🔍 Busca automáticamente los archivos CSV más recientes en `data/estadisticas_dnrpa/`
- 📦 Carga los datos a PostgreSQL
- 🔄 Evita duplicados (si ejecutas 2 veces, no duplica)
- ✅ Funciona con nombres dinámicos (ej: `*-2025-09.csv` o `*-2025-10.csv`)

---

## 🔄 Actualización Mensual (Futuro)

Cuando descargues archivos actualizados:

1. **Reemplaza los CSV** en `data/estadisticas_dnrpa/` con los nuevos
2. **Ejecuta el script** nuevamente:
   ```powershell
   python cargar_estadisticas_agregadas.py
   ```

El script automáticamente:
- ✅ Detectará los archivos más recientes
- ✅ Actualizará solo los registros modificados
- ✅ No duplicará datos existentes

---

## ✅ Verificar que Funcionó

```powershell
# Conectar a PostgreSQL
psql -h localhost -U postgres -d mercado_automotor

# Verificar datos cargados
SELECT COUNT(*) FROM estadisticas_inscripciones;
SELECT COUNT(*) FROM estadisticas_transferencias;

# Ver últimos 5 registros
SELECT * FROM estadisticas_inscripciones ORDER BY anio DESC, mes DESC LIMIT 5;

# Totales nacionales por año
SELECT anio, tipo_vehiculo, SUM(cantidad) as total
FROM estadisticas_inscripciones
GROUP BY anio, tipo_vehiculo
ORDER BY anio DESC;
```

---

## 📋 Estructura de las Tablas

### `estadisticas_inscripciones`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | ID autoincremental |
| `tipo_vehiculo` | VARCHAR(50) | 'Motovehículos' o 'Maquinarias' |
| `anio` | INTEGER | Año (2007-2025) |
| `mes` | INTEGER | Mes (1-12) |
| `provincia` | VARCHAR(100) | Nombre de la provincia |
| `letra_provincia` | VARCHAR(1) | Letra de patente (ej: 'B' para Buenos Aires) |
| `provincia_id` | VARCHAR(2) | Código de provincia (ej: '06') |
| `cantidad` | INTEGER | Total de inscripciones ese mes |
| `archivo_origen` | VARCHAR(255) | Nombre del CSV de origen |
| `fecha_carga` | TIMESTAMP | Cuándo se cargó |

### `estadisticas_transferencias`

Misma estructura pero para transferencias.

---

## 🎯 Próximo Paso

Una vez cargados los datos, se creará la pestaña **"📊 Tendencias Históricas"** en el dashboard de Streamlit con:

1. **Filtros:**
   - Tipo: Motovehículos / Maquinarias
   - Tipo de trámite: Inscripciones / Transferencias
   - Rango de años (2007-2025)
   - Provincias (selección múltiple)

2. **Gráficos:**
   - 📈 Serie temporal mensual (evolución 2007-2025)
   - 📊 Comparativa provincial (ranking histórico)
   - 🗺️ Mapa de calor estacional (mes vs año)
   - 🏆 Top 5 provincias

---

## ❓ Troubleshooting

### Error: "psql: command not found"
PostgreSQL no está en el PATH. Usa la ruta completa:
```powershell
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -h localhost -U postgres -d mercado_automotor -f sql/crear_tablas_estadisticas_agregadas.sql
```

### Error: "ModuleNotFoundError: No module named 'psycopg2'"
```powershell
pip install psycopg2-binary
```

### Error: "Connection refused"
PostgreSQL no está corriendo. Inícialo:
```powershell
# Si usas Docker
docker-compose up -d postgres

# Si está instalado localmente
# Services > PostgreSQL > Start
```

---

## 📝 Notas

- ✅ Los datos agregados son **complementarios** a los datos detallados
- ✅ Permiten análisis histórico desde 2007 (vs 2019 en datos detallados)
- ✅ Incluyen sector **Maquinarias** no disponible en datos detallados
- ✅ Consultas **súper rápidas** (18K registros vs 13.6M)
- ✅ Ideal para gráficos de tendencias y comparativas históricas

---

**¿Dudas?** Ejecuta los pasos y avísame si algo falla.
