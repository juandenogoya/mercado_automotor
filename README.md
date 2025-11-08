# Mercado Automotor - Sistema de Inteligencia Comercial

Sistema de análisis y monitoreo del mercado automotor argentino para gerencias comerciales.

## 🎯 Objetivos

- **Anticipar caídas de demanda**: Índice de tensión de demanda (ACARA + Google Trends + BCRA)
- **Detectar sobrestock**: Rotación estimada por terminal (ADEFA + ACARA)
- **Reforzar comunicación de marca**: Ranking de atención y búsqueda (Google Trends + Portales)
- **Ajustar precios y financiamiento**: Índice de accesibilidad de compra (BCRA + INDEC + Portales)

## 📊 Fuentes de Datos

| Fuente | Frecuencia | Tipo | Datos |
|--------|------------|------|-------|
| ACARA | Mensual | Web Scraping | Patentamientos 0km y usados |
| ADEFA | Mensual | Web Scraping | Producción y exportaciones |
| BCRA | Diaria | API REST | Tasas, créditos prendarios, indicadores |
| MercadoLibre | Diaria | API REST | Precios, listados, tendencias |

## 🏗️ Arquitectura

```
mercado_automotor/
├── backend/               # Python backend
│   ├── scrapers/         # Web scrapers (ACARA, ADEFA)
│   ├── api_clients/      # API clients (BCRA, MercadoLibre)
│   ├── models/           # Data models y ORM
│   ├── etl/              # ETL pipelines
│   ├── analytics/        # Modelos predictivos
│   └── utils/            # Utilities
├── frontend/             # Streamlit dashboard
├── database/             # SQL schemas y migrations
├── airflow/              # Airflow DAGs
├── docker/               # Docker configs
└── tests/                # Tests
```

## 🚀 Stack Tecnológico

### Backend
- Python 3.11+
- FastAPI (API REST interna)
- SQLAlchemy (ORM)
- Pandas, NumPy (procesamiento)
- Requests, BeautifulSoup4, Selenium (scraping)
- Scikit-learn, Statsmodels (ML/forecasting)

### Base de Datos
- PostgreSQL 15+
- TimescaleDB (series temporales)
- Redis (caché)

### Orquestación
- Apache Airflow (ETL scheduling)

### Frontend
- Streamlit (dashboards interactivos)
- Plotly (visualizaciones)

### DevOps
- Docker & Docker Compose
- GitHub Actions (CI/CD)

## 📦 Instalación

### Requisitos previos
- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (opcional)

### Setup con Docker (Recomendado)

```bash
# Clonar repositorio
git clone <repo-url>
cd mercado_automotor

# Copiar archivo de environment
cp .env.example .env

# Editar credenciales en .env

# Levantar servicios
docker-compose up -d

# Inicializar base de datos
docker-compose exec backend python manage.py init-db

# Acceder al dashboard
# http://localhost:8501
```

### Setup manual

```bash
# Crear virtual environment
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Inicializar base de datos
python manage.py init-db

# Ejecutar scrapers (primera carga)
python manage.py run-scrapers --all

# Iniciar dashboard
streamlit run frontend/app.py
```

## 🔧 Configuración

Editar [.env](.env):

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mercado_automotor

# APIs
MERCADOLIBRE_CLIENT_ID=your_client_id
MERCADOLIBRE_CLIENT_SECRET=your_client_secret

# Scraping
SCRAPING_USER_AGENT=MercadoAutomotorBot/1.0
SCRAPING_DELAY_SECONDS=5

# Dashboard
STREAMLIT_SERVER_PORT=8501
```

## 📈 Indicadores Disponibles

### 1. Índice de Tensión de Demanda
Combina patentamientos (ACARA), tasas de interés (BCRA) y tendencias de búsqueda para anticipar caídas.

### 2. Rotación Estimada por Terminal
Calcula días de stock promedio por marca comparando producción (ADEFA) vs. patentamientos (ACARA).

### 3. Índice de Accesibilidad de Compra
Relaciona precios de mercado (MercadoLibre), salarios (INDEC) y condiciones de financiamiento (BCRA).

### 4. Ranking de Atención de Marca
Analiza volumen de búsquedas y listados activos para identificar marcas/modelos en tendencia.

## 🔄 ETL Workflows

Los ETL se ejecutan automáticamente via Airflow:

- **Diarios** (00:00 hs): BCRA, MercadoLibre
- **Semanales** (Lunes 06:00 hs): Agregaciones, cálculo de índices
- **Mensuales** (Día 5, 08:00 hs): ACARA, ADEFA

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=backend --cov-report=html

# Tests específicos
pytest tests/test_scrapers.py
```

## 📚 Documentación

- [Guía de Desarrollo](docs/DEVELOPMENT.md)
- [API Endpoints](docs/API.md)
- [Modelos de Datos](docs/DATABASE.md)
- [Scrapers](docs/SCRAPERS.md)

## 🤝 Contribución

Este es un proyecto de consultoría privado. Para cambios, contactar al equipo de desarrollo.

## 📄 Licencia

Propietario - Todos los derechos reservados
