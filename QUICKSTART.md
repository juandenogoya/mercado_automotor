# 🚀 Guía de Inicio Rápido

Sistema de Inteligencia Comercial del Mercado Automotor Argentino

## 📋 Prerequisitos

- **Docker** y **Docker Compose** instalados
- **Python 3.11+** (para desarrollo local sin Docker)
- **PostgreSQL 15+** (para desarrollo local sin Docker)
- **Git**

## ⚡ Inicio Rápido con Docker (Recomendado)

### 1. Clonar el repositorio

```bash
cd c:\Users\juand\OneDrive\Escritorio\Concecionaria\mercado_automotor
```

### 2. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
copy .env.example .env

# Editar .env con tus credenciales (opcional para MVP)
notepad .env
```

### 3. Levantar servicios con Docker Compose

```bash
# Construir y levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 4. Acceder a los servicios

Una vez que todos los contenedores estén ejecutándose:

- **Dashboard Streamlit**: http://localhost:8501
- **API REST (FastAPI)**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Airflow Web UI**: http://localhost:8080 (usuario: `admin`, password: `admin`)
- **PostgreSQL**: localhost:5432 (usuario: `postgres`, password: `postgres`)

### 5. Inicializar base de datos

```bash
# Ejecutar dentro del contenedor backend
docker-compose exec backend python -c "from backend.utils.database import init_db; init_db()"
```

### 6. Ejecutar primera carga de datos (opcional)

```bash
# Trigger manual del DAG de sincronización completa en Airflow UI
# O ejecutar manualmente:

docker-compose exec backend python -c "
from backend.api_clients import BCRAClient
from datetime import date, timedelta

client = BCRAClient()
result = client.sync_all_indicators(
    fecha_desde=date.today() - timedelta(days=30),
    fecha_hasta=date.today()
)
print(result)
"
```

## 🛠️ Desarrollo Local (Sin Docker)

### 1. Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar PostgreSQL local

```sql
-- Conectarse a PostgreSQL
psql -U postgres

-- Crear base de datos
CREATE DATABASE mercado_automotor;

-- Crear base de datos para Airflow
CREATE DATABASE airflow;
```

### 4. Configurar variables de entorno

```bash
# Editar .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mercado_automotor
```

### 5. Inicializar base de datos

```bash
python -c "from backend.utils.database import init_db; init_db()"
```

### 6. Ejecutar servicios

**Terminal 1 - Backend API:**
```bash
cd backend
python main.py
# O con uvicorn:
# uvicorn backend.main:app --reload
```

**Terminal 2 - Dashboard:**
```bash
streamlit run frontend/app.py
```

**Terminal 3 - Airflow (opcional):**
```bash
# Exportar AIRFLOW_HOME
set AIRFLOW_HOME=%CD%\airflow

# Inicializar Airflow DB
airflow db init

# Crear usuario admin
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com

# Iniciar webserver
airflow webserver --port 8080

# En otra terminal, iniciar scheduler
airflow scheduler
```

## 📊 Estructura del Proyecto

```
mercado_automotor/
├── backend/                    # Backend Python
│   ├── api_clients/           # Clientes API (BCRA, MercadoLibre)
│   ├── scrapers/              # Web scrapers (ACARA, ADEFA)
│   ├── models/                # Modelos de base de datos (SQLAlchemy)
│   ├── config/                # Configuración
│   ├── utils/                 # Utilidades
│   └── main.py               # FastAPI app
├── frontend/                  # Dashboard Streamlit
│   └── app.py                # App principal
├── airflow/                   # Airflow DAGs
│   └── dags/                 # Definiciones de DAGs
├── database/                  # Scripts SQL
│   └── init_schema.sql       # Schema inicial
├── docker/                    # Dockerfiles
├── data/                      # Datos (no en git)
│   ├── raw/                  # Datos crudos
│   └── processed/            # Datos procesados
├── logs/                      # Logs (no en git)
├── docker-compose.yml        # Orquestación Docker
├── requirements.txt          # Dependencias Python
├── .env.example              # Template de variables de entorno
└── README.md                 # Documentación principal
```

## 🔑 Funcionalidades Implementadas

### ✅ MVP - Fase 1 + 2

1. **Scrapers Web**
   - ACARA: Patentamientos de 0km y usados
   - ADEFA: Producción y exportaciones

2. **Clientes API**
   - BCRA: Indicadores económicos y financieros
   - MercadoLibre: Listados y precios de mercado

3. **Base de Datos**
   - PostgreSQL con TimescaleDB
   - Modelos para todas las fuentes
   - Índices optimizados para queries temporales

4. **ETL Automatizado**
   - Airflow DAGs para scraping diario/mensual
   - Manejo de errores y retries
   - Logging estructurado

5. **API REST (FastAPI)**
   - Endpoints para todas las fuentes
   - Documentación automática (Swagger)
   - CORS habilitado

6. **Dashboard Interactivo (Streamlit)**
   - Resumen ejecutivo
   - Análisis de patentamientos
   - Indicadores BCRA
   - Análisis de MercadoLibre
   - Gráficos interactivos con Plotly

7. **Infraestructura Docker**
   - Multi-container con Docker Compose
   - PostgreSQL + Redis + Backend + Frontend + Airflow
   - Volúmenes persistentes

## 🎯 Indicadores Estratégicos (En desarrollo)

Los siguientes indicadores están planificados para desarrollo futuro:

1. **Índice de Tensión de Demanda**
   - Combina: ACARA + Google Trends + BCRA
   - Objetivo: Anticipar caídas de demanda

2. **Rotación Estimada por Terminal**
   - Combina: ADEFA + ACARA
   - Objetivo: Detectar sobrestock

3. **Índice de Accesibilidad de Compra**
   - Combina: BCRA + INDEC + MercadoLibre
   - Objetivo: Ajustar precios y financiamiento

4. **Ranking de Atención de Marca**
   - Combina: Google Trends + MercadoLibre
   - Objetivo: Reforzar comunicación de marca

## 🐛 Troubleshooting

### Error: Puerto 5432 ya está en uso

```bash
# Windows
netstat -ano | findstr :5432
taskkill /PID <PID> /F

# O cambiar el puerto en docker-compose.yml
ports:
  - "5433:5432"
```

### Error: Selenium WebDriver no funciona

```bash
# Verificar que Chrome/Chromium está instalado
# En Docker ya está incluido
# En local, instalar Chrome y chromedriver
```

### Error: No se pueden cargar datos en el dashboard

```bash
# Verificar que la base de datos tiene datos
docker-compose exec postgres psql -U postgres -d mercado_automotor -c "SELECT COUNT(*) FROM patentamientos;"

# Si no hay datos, ejecutar scrapers manualmente
```

## 📚 Próximos Pasos

1. **Configurar credenciales de MercadoLibre**
   - Registrarse en: https://developers.mercadolibre.com.ar/
   - Crear aplicación
   - Agregar `MERCADOLIBRE_CLIENT_ID` y `MERCADOLIBRE_CLIENT_SECRET` en `.env`

2. **Contactar a ACARA/ADEFA**
   - Solicitar permiso formal para scraping
   - Validar estructura actual de sus sitios web
   - Ajustar scrapers según estructura real

3. **Desarrollar modelos predictivos**
   - Implementar forecasting con Prophet/ARIMA
   - Calcular indicadores estratégicos
   - Crear alertas automáticas

4. **Configurar alertas y notificaciones**
   - Email/Slack cuando se detectan anomalías
   - Reportes automatizados semanales/mensuales

5. **Optimizar performance**
   - Implementar caché con Redis
   - Optimizar queries de base de datos
   - Implementar paginación en API

## 📞 Soporte

Para reportar bugs o solicitar features:
- Crear issue en el repositorio
- Contactar al equipo de desarrollo

---

**Versión MVP:** 1.0.0
**Fecha:** Noviembre 2025
**Stack:** Python 3.11 | PostgreSQL | FastAPI | Streamlit | Airflow | Docker
