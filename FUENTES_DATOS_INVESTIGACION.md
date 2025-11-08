# Investigación de Fuentes de Datos del Mercado Automotor Argentino

## Resumen Ejecutivo

Este documento presenta un análisis detallado de las principales fuentes de datos públicas del mercado automotor argentino, incluyendo métodos de acceso técnico, formatos de datos, limitaciones y recomendaciones de implementación.

---

## 1. ACARA / FACCARA - Estadísticas de Patentamientos

### Información General

**ACARA (Asociación de Concesionarios de Automotores de la República Argentina)**
- Fundada: 24 de agosto de 1944
- Tipo: Asociación civil sin fines de lucro
- Miembros: Concesionarios oficiales de vehículos (mono-marca)
- URL Principal: https://www.acara.org.ar

**FACCARA (Federación de Asociaciones y Cámaras del Comercio Automotor)**
- Fundada: 1976
- Tipo: Federación que agrupa asociaciones regionales
- Miembros: Más de 4,000 socios (incluye concesionarios multimarca)
- URL Estadísticas: https://www.faccara.org.ar/estadisticas-0km-usados/

### Datos Publicados

**Cobertura:**
- Patentamientos de vehículos 0 km (nuevos)
- Transferencias de vehículos usados
- Datos por marca y modelo
- Series históricas desde 2008 hasta la actualidad
- Datos mensuales y anuales

**Estadísticas Recientes (2025):**
- Octubre 2025: 51,982 patentamientos (+16.9% interanual)
- Enero-Octubre 2025: 552,484 unidades (+55.1% vs 2024)

### Formato y Acceso a Datos

**Formato de Publicación:**
- La página de ACARA (acara.org.ar) requiere JavaScript para funcionar
- Datos organizados por mes y año
- Descarga de reportes mensuales (formato no confirmado, probablemente PDF/Excel)
- Acceso histórico disponible desde 1995

**Frecuencia de Actualización:**
- Mensual (aproximadamente entre el día 1-5 del mes siguiente)

### Método de Acceso Técnico

**Tipo:** Web Scraping necesario (No hay API pública)

**Implementación Recomendada:**
```python
# Estrategia 1: Selenium para sitios con JavaScript
from selenium import webdriver
from selenium.webdriver.common.by import By
# Navegar a acara.org.ar/estudios_economicos/estadisticas.php
# Esperar carga de JavaScript
# Extraer enlaces de descarga

# Estrategia 2: Requests + BeautifulSoup para FACCARA
import requests
from bs4 import BeautifulSoup
# Si los datos están en HTML estático en faccara.org.ar
```

**Consideraciones:**
- Verificar términos de uso antes de automatizar
- Implementar delays entre requests (2-5 segundos recomendado)
- Cachear datos para minimizar requests
- Los datos son considerados públicos (estadísticas sectoriales)

### Limitaciones

**Legales:**
- No hay términos de uso explícitos encontrados
- Datos de naturaleza pública/estadística
- Recomendado: contactar a info@faccara.org.ar o 4824-7272 para uso comercial

**Técnicas:**
- ACARA requiere JavaScript (headless browser necesario)
- No hay API estructurada
- Formato de descarga puede variar
- Posibles cambios en estructura HTML

---

## 2. ADEFA - Producción y Exportaciones

### Información General

**ADEFA (Asociación de Fábricas de Automotores)**
- URL Principal: https://adefa.org.ar
- URL Estadísticas: https://adefa.org.ar/es/estadisticas-mensuales
- Representa: Fabricantes de automotores en Argentina

### Datos Publicados

**Cobertura:**
- Producción nacional de vehículos
- Exportaciones e importaciones
- Ventas al mercado interno
- Datos acumulados mensuales

**IMPORTANTE - Limitaciones de Datos:**
- Desde julio 2015: NO publican estadísticas mensuales por marcas/modelos
- Desde marzo 2016: NO incluyen vehículos pesados (camiones y buses)
- Reportes anuales por marca/modelo se publican con 7 meses de demora
- Solo se publican totales mensuales agregados

**Estadísticas Recientes (2025):**
- Mayo 2025: 48,109 unidades producidas
- Enero-Mayo 2025: 207,630 vehículos fabricados
- Octubre 2025: 47,204 unidades (-10% intermensual)

### Formato y Acceso a Datos

**Formato de Publicación:**
- Página organizada por meses del año (2025, 2024, etc.)
- Tabla con columna "Mes" y "Descargas"
- Archivos descargables por mes (formato probablemente PDF/Excel)
- Acceso histórico desde 1995

**Frecuencia de Actualización:**
- Mensual (datos agregados)
- Anual (datos detallados por marca/modelo con 7 meses de retraso)

### Método de Acceso Técnico

**Tipo:** Web Scraping + Descarga de archivos (No hay API pública)

**Implementación Recomendada:**
```python
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. Scraping de la página de estadísticas
url = "https://adefa.org.ar/es/estadisticas-mensuales"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# 2. Extraer enlaces de descarga mensuales
# Buscar elementos <a> con enlaces a PDFs o Excel

# 3. Descargar archivos
# Si son PDF: usar PyPDF2 o pdfplumber para extraer datos
# Si son Excel: usar pandas.read_excel()

# 4. Parsear y estructurar datos
```

**Consideraciones:**
- Los enlaces de descarga están en el HTML pero pueden requerir autenticación de sesión
- Posible necesidad de headers personalizados para downloads
- Implementar sistema de versionado local para evitar re-descargas

### Limitaciones

**Legales:**
- No se encontraron términos de uso explícitos
- Datos estadísticos de naturaleza pública
- Recomendado: contactar a ADEFA para uso automatizado

**Técnicas:**
- No hay API estructurada
- Detalle limitado en reportes mensuales
- Datos desagregados tienen 7 meses de retraso
- Formato de archivos puede cambiar sin aviso
- No incluye vehículos pesados desde 2016

---

## 3. BCRA - Indicadores Financieros y Créditos

### Información General

**BCRA (Banco Central de la República Argentina)**
- URL Principal: https://www.bcra.gob.ar
- URL Catálogo APIs: https://www.bcra.gob.ar/BCRAyVos/catalogo-de-APIs-banco-central.asp
- Tipo: APIs oficiales públicas y gratuitas

### APIs Oficiales Disponibles

#### 3.1 API de Principales Variables (v4.0)

**Base URL:** `https://api.bcra.gob.ar/estadisticas/v2.0`

**Documentación:** https://www.bcra.gob.ar/Catalogo/Content/files/pdf/principales-variables-v4.pdf

**Datos Disponibles:**
- Reservas internacionales
- Base monetaria
- Circulación monetaria
- Depósitos en entidades financieras
- Préstamos al sector privado
- Tasas de interés
- Tipos de cambio de referencia

**Autenticación:** No requiere

**Rate Limit:** Sin límites documentados

**Formato:** JSON

**Endpoints Principales:**
```
GET /estadisticas/v2.0/principales-variables
GET /estadisticas/v2.0/datos-variables/{id_variable}
```

#### 3.2 API de Estadísticas Cambiarias (v1.0)

**Base URL:** `https://api.bcra.gob.ar/estadisticascambiarias/v1.0`

**Documentación:** https://www.bcra.gob.ar/Catalogo/Content/files/pdf/estadisticascambiarias-v1.pdf

**Datos Disponibles:**
- Cotizaciones de divisas
- Maestro de monedas
- Evolución de tipos de cambio por período

**Autenticación:** No requiere

**Formato:** JSON

**Endpoints Principales:**
```
GET /estadisticascambiarias/v1.0/Maestros/Monedas
GET /estadisticascambiarias/v1.0/Cotizaciones/{fecha}
GET /estadisticascambiarias/v1.0/Evolucion/{moneda}/{fecha_desde}/{fecha_hasta}
```

#### 3.3 API de Central de Deudores (v1.0)

**Base URL:** `https://api.bcra.gob.ar/centraldedeudores/v1.0`

**Documentación:** https://www.bcra.gob.ar/Catalogo/Content/files/pdf/central-deudores-v1.pdf

**Autenticación:** No requiere (para datos agregados)

### Datos Específicos del Sector Automotor

#### Créditos Prendarios

**Archivo CSV Directo:**
- URL: https://www.bcra.gob.ar/pdfs/BCRAyVos/PRENDARIOS.CSV
- Datos de stock de créditos prendarios automotor
- Actualización: Mensual
- Formato: CSV con separadores

**Datos de Regulación:**
- Comunicación A2586: Préstamos con garantía prendaria sobre automotor
- Sistema de amortización: Francés
- Base: 360 días para aplicar tasa anual

**Estadísticas Recientes:**
- Noviembre 2024: Stock de $2.9 billones de pesos
- Crecimiento: +212.6% interanual

### API Alternativa (No Oficial)

**estadisticasbcra.com**
- Base URL: `https://api.estadisticasbcra.com`
- Documentación: https://estadisticasbcra.com/api/documentacion
- **Requiere:** Token de autenticación (registro gratuito)
- **Rate Limit:** 100 consultas diarias
- **Vigencia Token:** 1 año
- **Ventaja:** Interfaz más simple y datos pre-procesados

### Método de Acceso Técnico

**Tipo:** API REST oficial (Recomendado)

**Implementación Recomendada:**

```python
import requests
import pandas as pd

# API Oficial BCRA - Principales Variables
base_url = "https://api.bcra.gob.ar/estadisticas/v2.0"

# No requiere autenticación
response = requests.get(f"{base_url}/principales-variables")
data = response.json()

# Estadísticas Cambiarias
cambio_url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0"
cotizacion = requests.get(f"{cambio_url}/Cotizaciones/2025-11-08")

# Créditos Prendarios (CSV directo)
prendarios_url = "https://www.bcra.gob.ar/pdfs/BCRAyVos/PRENDARIOS.CSV"
df_prendarios = pd.read_csv(prendarios_url, encoding='latin-1')

# Wrapper Python recomendado
# pip install bcraapi
from bcraapi import BCRA
bcra = BCRA()
reservas = bcra.get_reserves()
```

**Python Wrappers Disponibles:**
- `bcraapi` (PyPI): https://pypi.org/project/bcraapi/
- `BCRA-Wrapper`: https://github.com/Jaldekoa/BCRA-Wrapper

### Limitaciones

**Legales:**
- APIs públicas y gratuitas sin restricciones de uso
- Datos gubernamentales de acceso abierto
- No requiere atribución específica

**Técnicas:**
- No hay límites de rate documentados (usar con moderación)
- Sin autenticación = sin garantías de SLA
- Posibles cambios en estructura de endpoints sin aviso
- CSV de prendarios puede tener problemas de encoding (usar latin-1)
- No hay datos específicos por marca/modelo de vehículos financiados

---

## 4. MercadoLibre API - Análisis de Mercado

### Información General

**MercadoLibre Developers**
- URL Principal: https://developers.mercadolibre.com.ar
- Documentación: https://developers.mercadolibre.com.ar/en_us/api-docs
- País: Argentina (código: MLA)

### Datos Disponibles

**Categorías Vehículos:**
- **MLA1743:** "Autos, Motos y Otros" (categoría general)
- **MLA455863:** Motos transaccionales (solo vendedores autorizados)
- Dominio especial: **CARS_AND_VANS** (Argentina, Brasil, México, Uruguay)

**Información Accesible:**
- Listados de vehículos en venta
- Precios, descripciones, atributos
- Ubicación geográfica
- Historial de vendedor
- Estadísticas de vistas y favoritos (con autenticación)

### Formato y Acceso a Datos

**Base URL:** `https://api.mercadolibre.com`

**Endpoints Principales:**

```bash
# Búsqueda general en Argentina
GET https://api.mercadolibre.com/sites/MLA/search?category=MLA1743

# Búsqueda con filtros
GET https://api.mercadolibre.com/sites/MLA/search?category=MLA1743&q=toyota&state=good

# Obtener categorías
GET https://api.mercadolibre.com/sites/MLA/categories

# Árbol completo de categorías
GET https://api.mercadolibre.com/sites/MLA/all

# Detalles de un ítem
GET https://api.mercadolibre.com/items/{ITEM_ID}

# Predictor de categoría
POST https://api.mercadolibre.com/sites/MLA/category_predictor/predict
```

### Autenticación

**OAuth 2.0 Requerido para:**
- Publicar listados
- Acceder a estadísticas de ítems propios
- Gestionar ventas y reputación

**No Requiere Autenticación para:**
- Búsquedas públicas
- Consulta de ítems públicos
- Obtener categorías y atributos

**Formato del Header (cuando se requiere):**
```
Authorization: Bearer APP_USR-12345678-031820-X-12345678
```

**Documentación OAuth:**
https://developers.mercadolibre.com.ar/en_us/authentication-and-authorization

### Rate Limits

**Límites Reportados:**
- Sin límites diarios/mensuales documentados oficialmente
- Límite por minuto (no especificado exactamente)
- Recomendación: Implementar backoff exponencial
- Los límites se aplican por token de aplicación

**Límites de Listados:**
```
GET https://api.mercadolibre.com/marketplace/users/cap
```
Este endpoint muestra límites de publicaciones por vendedor (diferente de rate limits de API)

### Método de Acceso Técnico

**Tipo:** API REST oficial (Uso permitido y recomendado)

**Implementación Recomendada:**

```python
import requests
import time

BASE_URL = "https://api.mercadolibre.com"

# Búsqueda pública (sin autenticación)
def search_vehicles(query, category="MLA1743", offset=0, limit=50):
    params = {
        "category": category,
        "q": query,
        "offset": offset,
        "limit": limit
    }
    response = requests.get(f"{BASE_URL}/sites/MLA/search", params=params)
    return response.json()

# Paginación
def get_all_results(query, max_results=1000):
    results = []
    offset = 0
    limit = 50

    while offset < max_results:
        data = search_vehicles(query, offset=offset, limit=limit)
        results.extend(data.get('results', []))

        if len(data.get('results', [])) < limit:
            break

        offset += limit
        time.sleep(0.5)  # Rate limiting cortesía

    return results

# Obtener detalles de un vehículo
def get_vehicle_details(item_id):
    response = requests.get(f"{BASE_URL}/items/{item_id}")
    return response.json()

# Filtros avanzados
def search_with_filters():
    params = {
        "category": "MLA1743",
        "vehicle_year": "2020-*",
        "price": "*-5000000",  # Precio máximo
        "state": "Capital Federal",
        "sort": "price_asc"
    }
    response = requests.get(f"{BASE_URL}/sites/MLA/search", params=params)
    return response.json()
```

**Atributos del Dominio CARS_AND_VANS:**
- brand (marca)
- model (modelo)
- vehicle_year (año)
- kilometers (kilometraje)
- doors (puertas)
- transmission (transmisión)
- fuel_type (tipo de combustible)
- engine (motor)

### Limitaciones

**Legales - MUY IMPORTANTE:**

Los términos de servicio de MercadoLibre **PROHIBEN EXPLÍCITAMENTE:**

1. **Web Scraping:** "Se prohíbe a los desarrolladores el uso de robots, harvesters, spiders, scraping u otra tecnología para acceder al Contenido de Mercado Libre"

2. **Uso Competitivo:** No se puede usar la API para desarrollar servicios que compitan con MercadoLibre

3. **Solo API Oficial:** Los datos solo pueden obtenerse mediante el Programa de Desarrolladores oficial

**Términos de Servicio:**
- https://developers.mercadolibre.com.ar/en_us/mercado-libre-developer-terms-and-conditions

**Domicilio Legal:**
- Av. Caseros 3039, 2do piso, CABA, Argentina

**Consecuencias de Violación:**
- Bloqueo de IP
- Suspensión de cuenta de desarrollador
- Posibles acciones legales

**Técnicas:**
- Los listados requieren patente válida (7-8 caracteres)
- Marca y modelo son atributos obligatorios
- No hay acceso a datos históricos de precios sin autenticación especial
- Rate limits no documentados explícitamente
- Paginación máxima: típicamente 1000 resultados por búsqueda

**Recomendaciones:**
- Usar SOLO la API oficial
- Implementar exponential backoff para errores 429
- Cachear resultados para minimizar llamadas
- Respetar robots.txt y términos de servicio
- Para análisis de mercado, considerar alternativas complementarias

---

## 5. Google Trends - Tendencias de Búsqueda

### Información General

**Google Trends**
- URL: https://trends.google.com
- **NO hay API oficial pública**
- Acceso mediante biblioteca no oficial: `pytrends`

### Datos Disponibles

**Métricas:**
- Interest Over Time: Interés histórico indexado (0-100)
- Interest by Region: Interés por ubicación geográfica
- Related Topics: Temas relacionados a las búsquedas
- Related Queries: Consultas relacionadas
- Trending Searches: Búsquedas en tendencia actuales

**Aplicaciones para Sector Automotor:**
- Tendencias de búsqueda de marcas/modelos
- Comparación de interés entre modelos
- Estacionalidad de búsquedas
- Interés regional por tipos de vehículos
- Correlación con ventas reales

### Método de Acceso Técnico

**Tipo:** Scraping mediante biblioteca no oficial (pytrends)

**Implementación Recomendada:**

```python
# Instalación
# pip install pytrends

from pytrends.request import TrendReq
import pandas as pd
import time
from random import randint

# Configuración básica
pytrends = TrendReq(hl='es-AR', tz=180)

# Búsqueda simple
kw_list = ["Toyota Corolla", "Volkswagen Gol", "Fiat Cronos"]
pytrends.build_payload(kw_list, timeframe='today 12-m', geo='AR')

# Interest Over Time
interest_over_time = pytrends.interest_over_time()

# Interest by Region (provincias Argentina)
interest_by_region = pytrends.interest_by_region(resolution='REGION')

# Related Queries
related_queries = pytrends.related_queries()

# Trending Searches (Argentina)
trending_searches = pytrends.trending_searches(pn='argentina')

# ----- MEJORES PRÁCTICAS PARA EVITAR RATE LIMITS -----

# 1. Configurar con proxy (si se requiere alto volumen)
pytrends = TrendReq(
    hl='es-AR',
    tz=180,
    proxies=['https://34.203.233.13:80'],
    timeout=(10, 25)
)

# 2. Implementar delays entre requests
def safe_get_trends(keywords, delay=60):
    """Obtener trends con delay para evitar bloqueos"""
    results = []

    for i in range(0, len(keywords), 5):  # Google Trends max 5 keywords
        batch = keywords[i:i+5]

        try:
            pytrends.build_payload(batch, timeframe='today 12-m', geo='AR')
            data = pytrends.interest_over_time()
            results.append(data)

            # Delay aleatorio entre 60-90 segundos
            wait_time = randint(delay, delay + 30)
            print(f"Esperando {wait_time} segundos...")
            time.sleep(wait_time)

        except Exception as e:
            print(f"Error: {e}")
            print("Esperando 120 segundos antes de reintentar...")
            time.sleep(120)

    return pd.concat(results, axis=1) if results else pd.DataFrame()

# 3. Usar parámetro sleep en historical interest
historical_data = pytrends.get_historical_interest(
    kw_list,
    year_start=2023,
    month_start=1,
    day_start=1,
    hour_start=0,
    year_end=2025,
    month_end=11,
    day_end=8,
    hour_end=0,
    sleep=60  # 60 segundos entre cada request
)

# 4. Rotación de proxies (para alto volumen)
proxy_list = [
    'https://proxy1.com:8080',
    'https://proxy2.com:8080',
    'https://proxy3.com:8080'
]

def get_trends_with_proxy_rotation(keywords):
    for i, proxy in enumerate(proxy_list):
        try:
            pytrends = TrendReq(hl='es-AR', tz=180, proxies=[proxy])
            pytrends.build_payload(keywords, timeframe='today 12-m', geo='AR')
            return pytrends.interest_over_time()
        except:
            continue
    return None
```

### Rate Limits y Restricciones

**Límites Reportados (No Oficiales):**

1. **Umbral de Bloqueo:**
   - Aproximadamente 1,400 requests secuenciales de 4 horas
   - Algunos usuarios reportan bloqueo después de apenas 10 requests
   - El límite exacto varía y no es público

2. **Tiempo de Bloqueo:**
   - Bloqueo temporal por IP
   - Duración: típicamente 60-120 minutos

3. **Soluciones Recomendadas:**
   - **Delay mínimo:** 60 segundos entre requests (obligatorio una vez alcanzado el límite)
   - **Delay preventivo:** 30-60 segundos entre requests normales
   - **Sleep parameter:** Usar `sleep=60` en métodos que lo soporten
   - **Proxies:** Rotación de IPs mediante proxies residenciales
   - **Backoff factor:** 0.1 para retry automático [0.0s, 0.2s, 0.4s, ...]

4. **Variantes del Límite:**
   - 100 requests por 100 segundos por usuario (max ajustable a 1,000)
   - 10 requests por segundo por usuario (máximo)
   - **Nota:** Estos límites parecen aplicar a Google Analytics API, no Trends específicamente

### Bibliotecas Alternativas

```python
# simplifiedpytrends - Con manejo automático de rate limits
# pip install simplifiedpytrends
from simplifiedpytrends import TrendReq

# pytrends-async - Para requests asíncronos
# pip install pytrends-async
```

### Limitaciones

**Legales:**
- **No hay API oficial:** pytrends hace scraping no autorizado
- Google puede bloquear IPs sin previo aviso
- Términos de servicio de Google generalmente prohíben scraping automatizado
- **Riesgo legal:** Uso bajo responsabilidad propia

**Técnicas:**
- Rate limits agresivos y no documentados
- Límite de 5 keywords por request
- Datos indexados (no valores absolutos)
- Posibles cambios en la estructura HTML que rompen pytrends
- Granularidad limitada (no hay datos en tiempo real por minuto/hora)
- Los datos son relativos, no absolutos
- Sin garantía de disponibilidad del servicio

**Recomendaciones:**
- Usar solo para análisis exploratorio inicial
- No depender de esta fuente para producción crítica
- Implementar siempre manejo de errores robusto
- Considerar proxies residenciales para volumen alto
- Complementar con otras fuentes de datos más confiables
- Respetar delays de 60+ segundos entre requests
- Usar en horarios de baja demanda si es posible

---

## 6. Comparación y Recomendaciones

### Tabla Comparativa de Fuentes

| Fuente | API/Scraping | Autenticación | Rate Limit | Frecuencia | Confiabilidad | Legal |
|--------|--------------|---------------|------------|------------|---------------|-------|
| **ACARA/FACCARA** | Scraping | No | Sin límites documentados | Mensual | Alta (oficial) | ⚠️ Zona gris |
| **ADEFA** | Scraping | No | Sin límites documentados | Mensual | Alta (oficial) | ⚠️ Zona gris |
| **BCRA** | API REST | No | Sin límites | Variable | Muy Alta (gobierno) | ✅ Público |
| **MercadoLibre** | API REST | Sí (búsquedas básicas No) | ~100/min estimado | Tiempo real | Alta | ✅ Permitido (solo API) |
| **Google Trends** | Scraping no oficial | No | ~10 req/hora seguro | Tiempo real | Media | ❌ No autorizado |

### Estrategia de Implementación Recomendada

#### Fase 1: Fuentes Seguras y Estructuradas (Semana 1-2)

1. **BCRA API (Prioridad Alta)**
   - Implementar primero: APIs oficiales
   - Sin barreras legales o técnicas
   - Datos financieros y de crédito estructurados
   - Python wrapper: `pip install bcraapi`

2. **MercadoLibre API (Prioridad Alta)**
   - Registrar aplicación en developers.mercadolibre.com.ar
   - Implementar búsquedas públicas sin autenticación
   - Usar autenticación OAuth solo si es necesario
   - Respetar estrictamente rate limits

#### Fase 2: Scraping Responsable (Semana 3-4)

3. **ADEFA Scraping (Prioridad Media)**
   - Implementar scraper con Requests + BeautifulSoup
   - Parser para archivos PDF/Excel descargados
   - Sistema de caché local para evitar re-descargas
   - Delay de 5 segundos entre requests
   - Contactar a ADEFA para permiso formal

4. **ACARA/FACCARA Scraping (Prioridad Media)**
   - Implementar con Selenium (ACARA requiere JavaScript)
   - Alternativa: Scraping de FACCARA con Requests
   - Sistema de versionado de datos
   - Delay de 5 segundos entre requests
   - Contactar para permiso formal

#### Fase 3: Fuentes Complementarias (Opcional)

5. **Google Trends (Prioridad Baja)**
   - Solo para análisis exploratorio
   - NO usar en producción
   - Implementar delays de 60+ segundos
   - Considerar proxies para volumen alto
   - Tener plan B para cuando falle

### Arquitectura de Datos Recomendada

```
┌─────────────────────────────────────────────────────────┐
│                   ETL Pipeline                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [BCRA API] ──────────┐                                │
│                        │                                │
│  [MercadoLibre API] ──┼──> [Orchestrator] ──> [DB]    │
│                        │         │                      │
│  [ADEFA Scraper] ─────┤         │                      │
│                        │         └──> [Data Lake]       │
│  [ACARA Scraper] ─────┤                                │
│                        │                                │
│  [Google Trends] ─────┘ (Opcional)                     │
│                                                         │
└─────────────────────────────────────────────────────────┘

Stack Tecnológico:
- Orquestación: Apache Airflow / Prefect / Dagster
- Storage: PostgreSQL + MinIO/S3 (data lake)
- Processing: Python (pandas, requests, selenium)
- Scheduling: Cron jobs o task scheduler del orquestador
- Monitoring: Sentry + Custom logging
```

### Consideraciones Legales Generales

**Recomendaciones:**

1. **Contactar Directamente:**
   - ACARA: info@faccara.org.ar / 4824-7272
   - ADEFA: Formulario de contacto en adefa.org.ar
   - Explicar propósito del proyecto
   - Solicitar permiso formal por escrito

2. **Términos de Uso:**
   - Leer y respetar robots.txt de cada sitio
   - Identificar el user-agent de tu scraper
   - Implementar rate limiting respetuoso
   - No sobrecargar servidores

3. **Atribución:**
   - Citar fuentes en análisis publicados
   - No redistribuir datos sin permiso
   - Respetar derechos de propiedad intelectual

4. **Uso Comercial:**
   - APIs públicas del BCRA: permitido
   - MercadoLibre API: permitido (via API oficial)
   - ACARA/ADEFA scraping: consultar antes

### Código de Ejemplo Integrado

```python
# requirements.txt
# requests==2.31.0
# beautifulsoup4==4.12.2
# selenium==4.15.0
# pandas==2.1.3
# bcraapi==1.1.0
# pytrends==4.9.2

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MercadoAutomotorScraper:
    """
    Orquestador de fuentes de datos del mercado automotor argentino
    """

    def __init__(self):
        self.bcra_base_url = "https://api.bcra.gob.ar"
        self.meli_base_url = "https://api.mercadolibre.com"
        self.delay_seconds = 5

    # ============ BCRA API ============

    def get_bcra_prendarios(self) -> pd.DataFrame:
        """Obtener datos de créditos prendarios del BCRA"""
        try:
            url = "https://www.bcra.gob.ar/pdfs/BCRAyVos/PRENDARIOS.CSV"
            df = pd.read_csv(url, encoding='latin-1')
            logger.info(f"BCRA Prendarios: {len(df)} registros obtenidos")
            return df
        except Exception as e:
            logger.error(f"Error obteniendo datos BCRA: {e}")
            return pd.DataFrame()

    def get_bcra_principales_variables(self) -> Dict:
        """Obtener principales variables del BCRA"""
        try:
            url = f"{self.bcra_base_url}/estadisticas/v2.0/principales-variables"
            response = requests.get(url)
            response.raise_for_status()
            logger.info("BCRA Principales Variables obtenidas exitosamente")
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo principales variables: {e}")
            return {}

    # ============ MercadoLibre API ============

    def search_mercadolibre_vehicles(
        self,
        query: str = "",
        category: str = "MLA1743",
        limit: int = 50,
        max_results: int = 200
    ) -> List[Dict]:
        """Buscar vehículos en MercadoLibre"""
        results = []
        offset = 0

        while offset < max_results:
            try:
                params = {
                    "category": category,
                    "q": query,
                    "offset": offset,
                    "limit": limit
                }

                url = f"{self.meli_base_url}/sites/MLA/search"
                response = requests.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                batch_results = data.get('results', [])
                results.extend(batch_results)

                logger.info(f"MercadoLibre: {len(batch_results)} resultados (offset {offset})")

                if len(batch_results) < limit:
                    break

                offset += limit
                time.sleep(0.5)  # Rate limiting cortesía

            except Exception as e:
                logger.error(f"Error en búsqueda MercadoLibre: {e}")
                break

        logger.info(f"Total MercadoLibre: {len(results)} vehículos")
        return results

    # ============ ADEFA Scraper ============

    def scrape_adefa_monthly(self, year: int = 2025) -> Dict:
        """
        Scraping de estadísticas mensuales de ADEFA
        Nota: Requiere análisis del HTML real para implementación completa
        """
        try:
            url = f"https://adefa.org.ar/es/estadisticas-mensuales"
            headers = {
                'User-Agent': 'MercadoAutomotorResearch/1.0 (+mailto:contacto@example.com)'
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # TODO: Implementar parseo del HTML
            # Extraer enlaces de descarga de PDFs/Excel
            # Descargar archivos
            # Parsear contenido

            logger.info("ADEFA: Datos mensuales scrapeados")
            time.sleep(self.delay_seconds)

            return {"status": "success", "url": url}

        except Exception as e:
            logger.error(f"Error scraping ADEFA: {e}")
            return {"status": "error", "message": str(e)}

    # ============ Orquestador Principal ============

    def fetch_all_sources(self) -> Dict[str, any]:
        """Obtener datos de todas las fuentes"""
        logger.info("=== Iniciando recolección de datos ===")

        data = {}

        # 1. BCRA (más confiable, sin límites)
        logger.info("Obteniendo datos BCRA...")
        data['bcra_prendarios'] = self.get_bcra_prendarios()
        data['bcra_variables'] = self.get_bcra_principales_variables()

        # 2. MercadoLibre (con rate limiting)
        logger.info("Obteniendo datos MercadoLibre...")
        data['meli_vehicles'] = self.search_mercadolibre_vehicles(
            query="",
            max_results=200
        )

        # 3. ADEFA (scraping respetuoso)
        logger.info("Scraping ADEFA...")
        data['adefa_monthly'] = self.scrape_adefa_monthly()

        logger.info("=== Recolección completada ===")
        return data

# Uso
if __name__ == "__main__":
    scraper = MercadoAutomotorScraper()
    all_data = scraper.fetch_all_sources()

    # Guardar datos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # BCRA Prendarios
    if not all_data['bcra_prendarios'].empty:
        all_data['bcra_prendarios'].to_csv(
            f"data/bcra_prendarios_{timestamp}.csv",
            index=False
        )

    # MercadoLibre
    df_meli = pd.DataFrame(all_data['meli_vehicles'])
    if not df_meli.empty:
        df_meli.to_csv(f"data/meli_vehicles_{timestamp}.csv", index=False)

    logger.info(f"Datos guardados con timestamp {timestamp}")
```

---

## 7. Próximos Pasos

### Desarrollo Inmediato

1. **Crear estructura de proyecto:**
   ```
   mercado_automotor/
   ├── src/
   │   ├── scrapers/
   │   │   ├── bcra_api.py
   │   │   ├── mercadolibre_api.py
   │   │   ├── adefa_scraper.py
   │   │   └── acara_scraper.py
   │   ├── utils/
   │   │   ├── logging_config.py
   │   │   └── rate_limiter.py
   │   └── orchestrator.py
   ├── data/
   │   ├── raw/
   │   └── processed/
   ├── config/
   │   └── sources.yaml
   ├── tests/
   └── requirements.txt
   ```

2. **Implementar en orden:**
   - Día 1-2: BCRA API (más simple)
   - Día 3-4: MercadoLibre API
   - Día 5-7: ADEFA scraper
   - Día 8-10: ACARA/FACCARA scraper
   - Día 11-14: Testing e integración

3. **Configurar infraestructura:**
   - Base de datos PostgreSQL
   - Sistema de caché (Redis opcional)
   - Scheduler (Airflow o cron)
   - Monitoring (Sentry)

### Contactos Recomendados

Antes de implementar scraping, contactar:

1. **FACCARA:** info@faccara.org.ar / 4824-7272 / 9505 / 9589
2. **ADEFA:** Formulario en adefa.org.ar
3. **ACARA:** Consultar en www.acara.org.ar

Plantilla de email:
```
Asunto: Consulta sobre uso de estadísticas públicas para análisis de mercado

Estimados,

Mi nombre es [NOMBRE] y estoy desarrollando un proyecto de análisis del mercado
automotor argentino con fines [académicos/comerciales/investigación].

Me gustaría consultar sobre la posibilidad de acceder a sus estadísticas
publicadas de manera automatizada mediante [scraping web/API] para:
- [Describir uso específico]
- [Frecuencia de actualización deseada]
- [Alcance del proyecto]

¿Existe alguna API o formato estructurado de datos disponible? En caso de
requerir scraping web, ¿autorizan el acceso automatizado respetuoso?

Quedo a disposición para brindar más detalles sobre el proyecto.

Saludos cordiales,
[NOMBRE]
[CONTACTO]
```

---

## 8. Recursos Adicionales

### Documentación Oficial

- **BCRA APIs:** https://www.bcra.gob.ar/BCRAyVos/catalogo-de-APIs-banco-central.asp
- **MercadoLibre Developers:** https://developers.mercadolibre.com.ar
- **ADEFA:** https://adefa.org.ar/es/estadisticas-mensuales
- **FACCARA:** https://www.faccara.org.ar/estadisticas-0km-usados/

### Bibliotecas Python Recomendadas

```bash
# Core
pip install requests==2.31.0
pip install beautifulsoup4==4.12.2
pip install pandas==2.1.3

# Scraping
pip install selenium==4.15.0
pip install scrapy==2.11.0

# APIs específicas
pip install bcraapi==1.1.0
pip install pytrends==4.9.2

# Utilidades
pip install python-dotenv==1.0.0
pip install pydantic==2.5.0
pip install loguru==0.7.2

# Data processing
pip install openpyxl==3.1.2  # Para Excel
pip install pdfplumber==0.10.3  # Para PDFs
pip install lxml==4.9.3  # Parser HTML más rápido

# Scheduling (opcional)
pip install apache-airflow==2.7.3
pip install prefect==2.14.3
```

### Repositorios GitHub Útiles

- **BCRA API Python:** https://github.com/aledc7/BCRA-API
- **BCRA Wrapper:** https://github.com/Jaldekoa/BCRA-Wrapper
- **PyTrends:** https://github.com/GeneralMills/pytrends

---

## Resumen Final

### Fuentes Recomendadas por Prioridad

**Tier 1 - Uso Inmediato (Sin barreras):**
1. ✅ **BCRA API** - Oficial, gratuita, sin límites
2. ✅ **MercadoLibre API** - Oficial, permitida, búsquedas públicas sin auth

**Tier 2 - Implementar con Precaución:**
3. ⚠️ **ADEFA Scraping** - Contactar antes, scraping respetuoso
4. ⚠️ **ACARA/FACCARA Scraping** - Contactar antes, requiere JavaScript

**Tier 3 - Solo Análisis Exploratorio:**
5. ❌ **Google Trends** - No oficial, rate limits agresivos, no para producción

### Checklist de Implementación

- [ ] Registrar aplicación en MercadoLibre Developers
- [ ] Contactar a ADEFA por email para permiso de scraping
- [ ] Contactar a FACCARA por email para permiso de scraping
- [ ] Implementar BCRA API (más fácil, sin barreras)
- [ ] Implementar MercadoLibre API con rate limiting
- [ ] Desarrollar ADEFA scraper con parseo de PDF/Excel
- [ ] Desarrollar ACARA scraper con Selenium
- [ ] Configurar base de datos PostgreSQL
- [ ] Implementar sistema de logging y monitoring
- [ ] Crear scheduler para actualizaciones automáticas
- [ ] Documentar código y crear tests unitarios
- [ ] Configurar CI/CD para deployment

---

**Documento generado:** 2025-11-08
**Investigación realizada para:** Proyecto Mercado Automotor Argentino
**Próxima revisión recomendada:** Trimestral (APIs pueden cambiar)
