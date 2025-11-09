# 🕷️ Web Scraping de MercadoLibre

## 📋 Resumen

Dado que MercadoLibre cerró el acceso a su API pública en 2025, implementamos un **web scraper robusto** para obtener datos del mercado automotor retail.

---

## ✅ Características del Scraper

### 🛡️ Anti-Detección
- ✅ **Rotating User-Agents:** Rota entre 6 user agents reales
- ✅ **Rate Limiting:** Delays aleatorios de 3-7 segundos entre requests
- ✅ **Headers realistas:** Imita navegadores reales (Chrome, Firefox, Safari)
- ✅ **Random timing:** Variación aleatoria en delays

### 🔍 Detección de Bloqueos
El scraper detecta automáticamente:
- ✅ **Status 403:** IP o User-Agent bloqueado
- ✅ **Status 429:** Rate limit excedido
- ✅ **Status 503:** Servicio temporalmente no disponible
- ✅ **CAPTCHAs:** Detecta páginas de verificación
- ✅ **Firewalls:** Cloudflare y otros
- ✅ **Páginas de error de ML**
- ✅ **HTML anormalmente corto:** Bloqueo silencioso

### 📊 Datos Extraídos
- Título completo del vehículo
- Precio (convertido a número)
- Marca y modelo (inferidos del título)
- Año
- Condición (0km/usado)
- Ubicación (ciudad, provincia)
- URL e ID del listing
- Fecha del snapshot

### 💾 Integración con PostgreSQL
- Guarda automáticamente en la tabla `mercadolibre_listings`
- Evita duplicados (mismo item + misma fecha)
- Metadata completa con timestamps

---

## 🚀 Uso Básico

### 1. Traer el código

```powershell
git pull origin claude/review-project-advantages-011CUvWjZ32MibKBCTEhtWn8
```

### 2. Probar el scraper

```powershell
python test_mercadolibre_scraper.py
```

Este test:
- ✅ Scrapea Toyota (1 página)
- ✅ Guarda en PostgreSQL
- ✅ Scrapea vehículos 0km
- ✅ Muestra estadísticas de precios
- ✅ Detecta y reporta bloqueos

### 3. Uso programático

```python
from backend.scrapers import MercadoLibreScraper

# Crear scraper
scraper = MercadoLibreScraper()

# Buscar vehículos
result = scraper.search_vehicles(
    marca="Toyota",
    modelo="Hilux",
    condition="new",  # 'new' o 'used'
    max_pages=3
)

# Ver resultados
print(f"Total scrapeado: {result['total_scraped']}")
for item in result['items']:
    print(f"{item['title']} - ${item['price']:,.0f}")

# Guardar en BD
saved = scraper.save_to_database(result['items'])
print(f"Guardados: {saved} items")
```

### 4. Scrapear múltiples marcas

```python
result = scraper.scrape_and_save(
    marcas=['Toyota', 'Ford', 'Volkswagen'],
    max_items_per_marca=100
)

print(f"Total guardado: {result['total_saved']}")
```

---

## 🔍 Logging y Diagnóstico

### Niveles de Logging

**INFO:** Operaciones normales
```
[MercadoLibre Scraper] Inicializado
[Búsqueda] Iniciando scraping: marca=Toyota
[Página 1] Scrapeando: https://...
[Página 1] Status 200 - OK
[Resultado] Total items scrapeados: 47
```

**SUCCESS:** Operaciones exitosas
```
[Página 1] Status 200 - OK
[BD] Guardados 45 items nuevos
```

**WARNING:** Advertencias no críticas
```
[Página 3] No se encontraron items
[BLOQUEO POSIBLE] HTML muy corto, posible bloqueo silencioso
[BD] Item MLA123 ya existe para hoy
```

**ERROR:** Errores y bloqueos
```
[BLOQUEO] Status 403 Forbidden - IP o User-Agent bloqueado
[BLOQUEO] Status 429 Too Many Requests - Rate limit excedido
[BLOQUEO] CAPTCHA detectado en la página
[BLOQUEO] Cloudflare/Firewall detectado
```

### Ver Logs

```powershell
# Ver logs en tiempo real
tail -f logs/app.log

# Ver solo errores
grep ERROR logs/app.log

# Ver bloqueos
grep BLOQUEO logs/app.log
```

---

## 🚨 ¿Qué Hacer Si Te Bloquean?

### Identificar el Bloqueo

Buscar en logs:
```powershell
grep BLOQUEO logs/app.log
```

### Tipos de Bloqueo y Soluciones

#### 1. **Status 403 - IP Bloqueada**

**Síntoma:**
```
[BLOQUEO] Status 403 Forbidden - IP o User-Agent bloqueado
```

**Soluciones:**
1. **Esperar:** 15-30 minutos antes de reintentar
2. **Cambiar IP:**
   - Reiniciar router
   - Usar VPN
   - Usar proxy
3. **Aumentar delays:**
   Editar `.env`:
   ```env
   SCRAPING_DELAY_MIN=5
   SCRAPING_DELAY_MAX=10
   ```

#### 2. **Status 429 - Rate Limit**

**Síntoma:**
```
[BLOQUEO] Status 429 Too Many Requests - Rate limit excedido
```

**Soluciones:**
1. **Reducir velocidad:**
   ```env
   SCRAPING_DELAY_MIN=7
   SCRAPING_DELAY_MAX=15
   ```
2. **Scrapear menos páginas:** `max_pages=2`
3. **Esperar 1 hora** antes de reintentar

#### 3. **CAPTCHA**

**Síntoma:**
```
[BLOQUEO] CAPTCHA detectado en la página
```

**Soluciones:**
1. **Resolver manualmente:** Abrir ML en navegador, resolver CAPTCHA
2. **Cambiar IP**
3. **Esperar 30-60 minutos**
4. **Usar servicio de CAPTCHA solving** (avanzado, no recomendado)

#### 4. **Cloudflare/Firewall**

**Síntoma:**
```
[BLOQUEO] Cloudflare/Firewall detectado
```

**Soluciones:**
1. **Cambiar User-Agent:**
   El scraper rota automáticamente, pero si persiste, actualizar la lista en el código
2. **Usar Selenium** en lugar de requests (más lento pero más realista)
3. **Cambiar IP/VPN**

---

## ⚙️ Configuración Avanzada

### Ajustar Delays

En `.env`:
```env
# Delay mínimo entre requests (segundos)
SCRAPING_DELAY_MIN=3

# Delay máximo entre requests (segundos)
SCRAPING_DELAY_MAX=7

# Timeout de requests (segundos)
SCRAPING_TIMEOUT=30
```

**Recomendaciones:**
- **Conservador:** MIN=5, MAX=10 (más lento, más seguro)
- **Normal:** MIN=3, MAX=7 (balance)
- **Agresivo:** MIN=2, MAX=5 (más rápido, mayor riesgo)

### Usar Proxies (Avanzado)

```python
scraper = MercadoLibreScraper()

# Configurar proxy
scraper.session.proxies = {
    'http': 'http://proxy.ejemplo.com:8080',
    'https': 'https://proxy.ejemplo.com:8080'
}

# O con autenticación
scraper.session.proxies = {
    'http': 'http://usuario:pass@proxy.com:8080',
    'https': 'https://usuario:pass@proxy.com:8080'
}
```

### Rotating Proxies

```python
import random

proxies_list = [
    'http://proxy1.com:8080',
    'http://proxy2.com:8080',
    'http://proxy3.com:8080',
]

# Antes de cada request
scraper.session.proxies = {
    'http': random.choice(proxies_list),
    'https': random.choice(proxies_list)
}
```

---

## 📊 Automatización

### Scraping Diario con Cron (Linux/Mac)

```bash
# Editar crontab
crontab -e

# Agregar línea (scrapear a las 3 AM diariamente)
0 3 * * * cd /path/to/mercado_automotor && python scripts/scrape_mercadolibre.py
```

### Scraping Diario con Task Scheduler (Windows)

1. Crear script `scripts/scrape_mercadolibre.bat`:
   ```batch
   @echo off
   cd C:\path\to\mercado_automotor
   python scripts/scrape_mercadolibre.py
   ```

2. Abrir "Programador de tareas" (Task Scheduler)
3. Crear tarea básica
4. Trigger: Diario, 3:00 AM
5. Acción: Ejecutar `scrape_mercadolibre.bat`

### Con Airflow (Recomendado)

Crear DAG en `airflow/dags/mercadolibre_daily_scrape.py`:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def scrape_mercadolibre():
    from backend.scrapers import MercadoLibreScraper
    scraper = MercadoLibreScraper()
    result = scraper.scrape_and_save(
        marcas=['Toyota', 'Ford', 'Volkswagen', 'Chevrolet'],
        max_items_per_marca=200
    )
    return result

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(hours=1),
}

dag = DAG(
    'mercadolibre_daily_scrape',
    default_args=default_args,
    schedule_interval='0 3 * * *',  # 3 AM diario
    catchup=False
)

scrape_task = PythonOperator(
    task_id='scrape_ml',
    python_callable=scrape_mercadolibre,
    dag=dag
)
```

---

## 📈 Análisis de Datos Scrapeados

### Query SQL - Precios Promedio por Marca

```sql
SELECT
    marca,
    condicion,
    COUNT(*) as cantidad,
    AVG(precio) as precio_promedio,
    MIN(precio) as precio_min,
    MAX(precio) as precio_max
FROM mercadolibre_listings
WHERE fecha_snapshot = CURRENT_DATE
GROUP BY marca, condicion
ORDER BY cantidad DESC;
```

### Query SQL - Evolución de Precios

```sql
SELECT
    fecha_snapshot,
    marca,
    AVG(precio) as precio_promedio
FROM mercadolibre_listings
WHERE marca = 'Toyota'
  AND modelo LIKE '%Hilux%'
  AND condicion = 'new'
GROUP BY fecha_snapshot, marca
ORDER BY fecha_snapshot;
```

### Python - Análisis de Oferta

```python
from backend.utils.database import get_db
from backend.models.mercadolibre_listings import MercadoLibreListing
from sqlalchemy import func
from datetime import date

with get_db() as db:
    # Contar oferta por marca
    oferta = db.query(
        MercadoLibreListing.marca,
        func.count(MercadoLibreListing.id).label('cantidad')
    ).filter(
        MercadoLibreListing.fecha_snapshot == date.today()
    ).group_by(
        MercadoLibreListing.marca
    ).order_by(
        func.count(MercadoLibreListing.id).desc()
    ).limit(10).all()

    for marca, cantidad in oferta:
        print(f"{marca}: {cantidad} listings")
```

---

## 🎯 Mejores Prácticas

### ✅ DO
- ✅ Usar delays generosos (3-7 segundos)
- ✅ Scrapear durante horas de bajo tráfico (3-6 AM)
- ✅ Monitorear logs constantemente
- ✅ Guardar datos inmediatamente en BD
- ✅ Implementar retry logic con backoff exponencial
- ✅ Respetar rate limits

### ❌ DON'T
- ❌ Scrapear sin delays
- ❌ Hacer requests paralelas
- ❌ Ignorar mensajes de bloqueo
- ❌ Scrapear durante horas pico
- ❌ Re-scrapear mismos datos múltiples veces al día
- ❌ Ignorar errores 429/503

---

## 🔧 Troubleshooting

### Problema: "No se encontraron items"

**Posibles causas:**
1. MercadoLibre cambió estructura HTML
2. Búsqueda sin resultados
3. Bloqueo silencioso

**Solución:**
```python
# Verificar que la URL sea correcta
result = scraper.search_vehicles(marca="Toyota", max_pages=1)
if result['items']:
    print(result['items'][0])  # Ver estructura
```

### Problema: "HTML muy corto"

**Causa:** Bloqueo silencioso o página vacía

**Solución:**
1. Verificar URL manualmente en navegador
2. Esperar 30 minutos
3. Cambiar IP

### Problema: Items sin precio

**Causa:** Estructura HTML diferente

**Solución:**
- Actualizar selectores en `_parse_item()`
- Verificar HTML manualmente
- Reportar para actualizar scraper

---

## 📞 Soporte

Si encontrás problemas:
1. Revisar logs: `logs/app.log`
2. Buscar mensajes de BLOQUEO
3. Verificar configuración en `.env`
4. Probar con delays más altos

---

## ⚖️ Consideraciones Legales

⚠️ **IMPORTANTE:** Web scraping puede estar sujeto a términos de servicio.

- Usá el scraper de forma ética y responsable
- Respetá rate limits
- No sobrecargues los servidores de ML
- Los datos son solo para análisis privado
- No redistribuir datos scrapeados sin autorización

---

## 🚀 Próximos Pasos

Una vez que el scraper funcione:

1. **Automatizar scraping diario**
2. **Crear dashboard Streamlit** con datos scraped
3. **Combinar con datos.gob.ar** para análisis completo
4. **Alertas automáticas** de oportunidades
5. **Análisis de tendencias** de precios

¡Éxito con el scraping! 🕷️
