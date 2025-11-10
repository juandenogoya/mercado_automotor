# 📊 Dashboard de Análisis - datos.gob.ar

Dashboard interactivo para análisis de trámites automotores de Argentina.

**Fuente:** datos.gob.ar - DNRPA (Dirección Nacional de Registro de Propiedad del Automotor)

---

## 🎯 Características

### 4 Pestañas de Análisis

1. **🚗 Inscripciones** - Patentamientos de vehículos 0km
2. **🔄 Transferencias** - Transferencias de vehículos usados
3. **💰 Prendas** - Prendas sobre vehículos
4. **📍 Registros Seccionales** - Catálogo de oficinas de registro

### Filtros Avanzados

- ✅ **Años múltiples** - Selecciona 2020, 2024, 2025, etc.
- ✅ **Meses múltiples** - Elige Enero, Marzo, Diciembre, etc.
- ✅ **Provincias múltiples** - Compara Corrientes, Entre Ríos, Buenos Aires, etc.

### Visualizaciones

#### 📈 Comparación Year over Year (YoY)
- Gráfico de barras por año
- Métricas de variación porcentual entre años

#### 📅 Evolución Mensual
- Gráfico de líneas de Enero a Diciembre
- **Líneas de diferente color por cada año seleccionado**
- Permite comparar patrones mensuales entre años

#### 🗺️ Análisis Provincial
- Gráfico de barras horizontal por provincia
- Gráfico de torta de distribución
- Evolución mensual comparativa entre provincias

#### 🏆 Top Marcas
- Ranking de las 10 marcas más tramitadas

#### 📊 KPIs Principales
- Total de trámites
- Promedio mensual
- Cantidad de provincias, marcas, tipos de vehículo

---

## 🚀 Inicio Rápido

### Opción 1: Script de Lanzamiento

```bash
python ejecutar_dashboard_datos_gob.py
```

### Opción 2: Comando Directo

```bash
streamlit run frontend/app_datos_gob.py
```

### Opción 3: Con puerto personalizado

```bash
streamlit run frontend/app_datos_gob.py --server.port 8502
```

---

## 📋 Requisitos Previos

### 1. Datos Cargados en PostgreSQL

El dashboard requiere que los datos estén cargados en las siguientes tablas:

- `datos_gob_inscripciones`
- `datos_gob_transferencias`
- `datos_gob_prendas`
- `datos_gob_registros_seccionales`

### 2. Cargar Datos

Si aún no tienes datos cargados:

```bash
# 1. Descargar datos CSV desde datos.gob.ar
# Buscar: "Estadística de trámites de automotores"

# 2. Organizar archivos en carpetas
mercado_automotor/INPUT/
├── INSCRIPCIONES/
│   └── *.csv
├── TRANSFERENCIAS/
│   └── *.csv
└── PRENDAS/
    └── *.csv

# 3. Ejecutar carga a PostgreSQL
python cargar_datos_gob_ar_postgresql.py
```

### 3. PostgreSQL en Ejecución

Asegúrate que PostgreSQL esté corriendo:

```bash
# Con Docker
docker-compose up -d postgres

# O servicio local
sudo service postgresql start  # Linux
brew services start postgresql # macOS
```

---

## 💡 Casos de Uso

### Ejemplo 1: Comparar Patentamientos 2024 vs 2025

1. Ir a pestaña **🚗 Inscripciones**
2. Seleccionar años: `2024, 2025`
3. Seleccionar meses: `Enero, Febrero, ..., Diciembre`
4. Seleccionar provincias de interés
5. Ver:
   - **Gráfico YoY**: Barras comparando totales anuales
   - **Evolución Mensual**: Líneas de diferente color (azul 2024, naranja 2025)
   - **Variación %**: Métrica YoY en la columna derecha

### Ejemplo 2: Análisis Estacional

1. Selecciona varios años: `2020, 2021, 2022, 2023, 2024`
2. Selecciona todos los meses
3. Selecciona 1 provincia (ejemplo: Buenos Aires)
4. Observa el gráfico de **Evolución Mensual**:
   - 5 líneas de colores diferentes (una por año)
   - Identifica patrones: ¿Cuáles meses tienen picos? ¿Cuáles caídas?
   - Compara: ¿El patrón es similar entre años?

### Ejemplo 3: Comparación Regional

1. Selecciona 1 año: `2024`
2. Selecciona todos los meses
3. Selecciona múltiples provincias: `Corrientes, Entre Ríos, Santa Fe, Buenos Aires`
4. Ve a la sección **"Comparación Mensual entre Provincias"**:
   - Gráfico de líneas con 4 colores (uno por provincia)
   - Identifica provincias con mayor actividad
   - Detecta comportamientos atípicos por región

### Ejemplo 4: Análisis de Tendencias MoM (Month over Month)

1. Selecciona 1 año: `2024`
2. Selecciona meses consecutivos: `Enero, Febrero, Marzo, Abril`
3. Selecciona 1 provincia
4. En la tabla de datos detallados:
   - Ordena por mes
   - Compara valores consecutivos manualmente
   - Identifica crecimientos o caídas mensuales

---

## 📊 Estructura de Datos

### Columnas Disponibles

Todas las tablas (inscripciones, transferencias, prendas) tienen:

```
Trámite:
- tramite_tipo
- tramite_fecha
- fecha_inscripcion_inicial

Registro Seccional:
- codigo
- descripcion
- provincia

Automotor:
- origen
- anio_modelo
- tipo (código y descripción)
- marca (código y descripción)
- modelo (código y descripción)
- uso (código y descripción)

Titular:
- tipo_persona
- domicilio (localidad, provincia)
- genero
- anio_nacimiento
- pais_nacimiento
- porcentaje_titularidad
```

---

## 🎨 Visualizaciones Explicadas

### Gráfico de Barras - Comparación Anual
**¿Qué muestra?**
Total de trámites por año seleccionado.

**¿Cómo interpretarlo?**
- Barras más altas = Mayor actividad
- Compara alturas para ver años con más/menos trámites

### Gráfico de Líneas - Evolución Mensual
**¿Qué muestra?**
Evolución de Enero a Diciembre, con una línea por cada año.

**¿Cómo interpretarlo?**
- Cada línea = Un año
- Picos = Meses con alta actividad
- Valles = Meses con baja actividad
- Líneas paralelas = Comportamiento similar entre años
- Líneas divergentes = Comportamientos diferentes

### Gráfico de Barras Horizontal - Provincias
**¿Qué muestra?**
Ranking de provincias por total de trámites.

**¿Cómo interpretarlo?**
- Barras más largas = Provincias con más actividad
- Útil para identificar mercados principales

### Gráfico de Torta - Distribución
**¿Qué muestra?**
Participación porcentual de cada provincia/categoría.

**¿Cómo interpretarlo?**
- Porciones más grandes = Mayor participación
- Rápida visualización de concentración de mercado

---

## 🔍 Filtros y Funcionalidades

### Filtros Múltiples

**Años:**
- Selecciona 1 o más años
- Útil para comparaciones YoY
- Ejemplo: `2023, 2024, 2025`

**Meses:**
- Selecciona meses específicos
- Ejemplo: Solo trimestres: `Ene, Abr, Jul, Oct`
- O solo primer semestre: `Ene, Feb, Mar, Abr, May, Jun`

**Provincias:**
- Selecciona regiones de interés
- Ejemplo: NEA: `Corrientes, Misiones, Formosa, Chaco`
- O zona centro: `Córdoba, Santa Fe, Buenos Aires`

### Búsqueda en Registros Seccionales

En la pestaña **📍 Registros Seccionales**:
- Busca por denominación o localidad
- Ejemplo: "Centro" encuentra todos los registros con "Centro" en el nombre
- Filtra por provincia

---

## 📥 Descarga de Datos

Cada pestaña incluye botón de descarga:

**📥 Descargar datos (CSV)**

El archivo incluye:
- Datos filtrados según selección actual
- Formato CSV compatible con Excel
- Columnas: Año, Mes, Provincia, Marca, Tipo Vehículo, Cantidad
- Nombre del archivo con timestamp: `datos_gob_inscripciones_20250110_143022.csv`

---

## 🐛 Troubleshooting

### Error: "No hay datos disponibles"

**Causa:** La tabla está vacía.

**Solución:**
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Cargar datos
python cargar_datos_gob_ar_postgresql.py
```

### Error: "Connection refused"

**Causa:** PostgreSQL no está corriendo o configuración incorrecta.

**Solución:**
```bash
# Verificar .env tiene:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mercado_automotor
DB_USER=postgres
DB_PASSWORD=postgres

# Iniciar PostgreSQL
docker-compose up -d postgres
```

### Dashboard no se abre en navegador

**Causa:** Puerto 8501 ocupado o configuración de firewall.

**Solución:**
```bash
# Usar puerto alternativo
streamlit run frontend/app_datos_gob.py --server.port 8502

# O abrir manualmente
http://localhost:8501
```

### Datos cargados pero no aparecen

**Causa:** Filtros muy restrictivos.

**Solución:**
1. Amplía selección de años
2. Selecciona todos los meses
3. Selecciona más provincias
4. Verifica que `tramite_fecha` no sea NULL en la BD

---

## 📈 Próximas Mejoras

### En desarrollo
- [ ] Exportar gráficos como PNG
- [ ] Comparación MoM automática en métricas
- [ ] Filtro por tipo de vehículo
- [ ] Filtro por marca
- [ ] Análisis de correlación entre variables
- [ ] Forecast de tendencias con Prophet

### Sugerencias

¿Tienes ideas para mejorar el dashboard? Abre un issue en el repositorio.

---

## 📞 Soporte

**Dataset oficial:**
https://datos.gob.ar - Buscar "Estadística de trámites de automotores"

**Documentación PostgreSQL:**
Ver `/sql/crear_tablas_datos_gob_ar.sql`

**Estructura del proyecto:**
Ver `/RESUMEN_PROYECTO.md`

---

## 📄 Licencia

Este dashboard es parte del proyecto **Mercado Automotor - Sistema de Inteligencia Comercial**.

Datos públicos proporcionados por datos.gob.ar bajo términos de uso de datos abiertos.

---

**Desarrollado con:**
- Streamlit 🎈
- Plotly 📊
- Pandas 🐼
- PostgreSQL 🐘
- Python 🐍

**Versión:** 1.0.0
**Fecha:** Noviembre 2025
