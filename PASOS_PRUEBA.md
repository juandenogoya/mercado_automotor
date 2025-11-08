# 🧪 Guía Paso a Paso - Prueba del Sistema

## ✅ Pre-requisitos Verificados
- ✅ PostgreSQL instalado
- ✅ pgAdmin4 instalado
- ✅ Entorno virtual Python creado
- ⏳ Dependencias instalándose...

---

## 📋 Pasos para Probar el Sistema Completo

### Paso 1: Esperar a que termine la instalación de dependencias

Verifica que terminó con:
```bash
venv\Scripts\pip.exe list
```

Si ves una lista larga de paquetes, está listo. Si dice "Installing...", espera un poco más.

---

### Paso 2: Crear la Base de Datos

**Opción A: Usando pgAdmin4 (GUI)**

1. Abre **pgAdmin4**
2. Conéctate a tu servidor PostgreSQL local
3. Click derecho en "Databases" → "Create" → "Database"
4. Nombre: `mercado_automotor`
5. Owner: `postgres` (o tu usuario)
6. Click "Save"

**Opción B: Usando psql (Línea de comandos)**

```bash
# Conectarse a PostgreSQL
psql -U postgres

# Crear base de datos
CREATE DATABASE mercado_automotor;

# Salir
\q
```

**Opción C: Ejecutar script SQL**

En pgAdmin4:
1. Click derecho en el servidor → "Query Tool"
2. Abrir archivo: `setup_database.sql`
3. Ejecutar (F5)

---

### Paso 3: Configurar Variables de Entorno

El archivo `.env` ya está creado, pero verifica que tenga la configuración correcta de PostgreSQL:

```bash
# Abre .env en un editor de texto y verifica:
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/mercado_automotor
```

**⚠️ IMPORTANTE:** Reemplaza `TU_PASSWORD` con tu contraseña de PostgreSQL.

---

### Paso 4: Probar Instalación Básica (SIN Base de Datos)

```bash
# Activar entorno virtual
venv\Scripts\activate

# Ejecutar script de prueba
python test_setup.py
```

**Deberías ver:**
```
🧪 PRUEBA DE INSTALACIÓN - Mercado Automotor
============================================================

1️⃣  Probando imports básicos...
   ✅ Pandas, NumPy, Requests, BeautifulSoup OK

2️⃣  Probando FastAPI...
   ✅ FastAPI OK

... (más pruebas)

9️⃣  Probando conexión real a API BCRA...
   ✅ API BCRA respondió correctamente (X variables obtenidas)

🔟 Probando conexión real a API MercadoLibre...
   ✅ API MercadoLibre respondió correctamente

✅ TODAS LAS PRUEBAS COMPLETADAS
```

---

### Paso 5: Inicializar Base de Datos

```bash
# Con el entorno virtual activado
python manage.py init-db
```

**Deberías ver:**
```
Inicializando base de datos...
✓ Base de datos inicializada correctamente
```

**Verificar en pgAdmin4:**
1. Refresh en "mercado_automotor" → "Schemas" → "public" → "Tables"
2. Deberías ver 5 tablas:
   - `patentamientos`
   - `produccion`
   - `bcra_indicadores`
   - `mercadolibre_listings`
   - `indicadores_calculados`

---

### Paso 6: Probar Cliente BCRA (Datos Reales)

```bash
# Ejecutar scraper de BCRA
python manage.py run-scrapers --source bcra
```

**Deberías ver:**
```
Ejecutando scrapers: bcra
Ejecutando BCRA sync...
[BCRA] Sincronizando indicadores desde YYYY-MM-DD hasta YYYY-MM-DD...
[BCRA] ✓ tasa_badlar: X registros guardados
[BCRA] ✓ Sincronización completada: X registros guardados
```

**Verificar en la base de datos:**
```bash
# Ver estadísticas
python manage.py stats
```

O en pgAdmin4:
```sql
SELECT COUNT(*) FROM bcra_indicadores;
SELECT * FROM bcra_indicadores LIMIT 10;
```

---

### Paso 7: Probar Cliente MercadoLibre (Datos Reales)

```bash
# Ejecutar scraper de MercadoLibre (solo 2 marcas para prueba rápida)
python -c "
from backend.api_clients.mercadolibre_client import MercadoLibreClient

client = MercadoLibreClient()
result = client.scrape_market_snapshot(
    marcas=['Toyota', 'Ford'],
    max_items_por_marca=20
)
print(result)
"
```

**Deberías ver:**
```
[MercadoLibre] Iniciando snapshot del mercado...
[MercadoLibre] Procesando marca: Toyota
[MercadoLibre] ✓ Toyota: 20 items procesados
[MercadoLibre] Procesando marca: Ford
[MercadoLibre] ✓ Ford: 20 items procesados
[MercadoLibre] ✓ Snapshot completado: 40 items guardados
```

---

### Paso 8: Ejecutar Dashboard de Streamlit 🎉

```bash
# Iniciar dashboard
python manage.py run-dashboard
```

**O directamente con streamlit:**
```bash
streamlit run frontend/app.py
```

**Deberías ver:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.X.X:8501
```

**Abre tu navegador en:** http://localhost:8501

**Deberías ver:**
- 📊 Dashboard con título "Dashboard Ejecutivo - Mercado Automotor"
- 4 KPIs en la parte superior
- Gráficos de patentamientos
- Top 10 marcas
- Pestañas con indicadores estratégicos

---

### Paso 9: Ejecutar API REST (Opcional)

```bash
# En otra terminal (con venv activado)
python manage.py run-api
```

**Abre tu navegador en:**
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Prueba un endpoint:**
- http://localhost:8000/api/bcra/indicadores

---

### Paso 10: Probar Scrapers ACARA/ADEFA (Opcional)

**⚠️ NOTA:** Estos scrapers requieren ajustar a la estructura real de los sitios.

```bash
# Probar ACARA (puede fallar si el sitio cambió)
python manage.py run-scrapers --source acara

# Probar ADEFA (puede fallar si el sitio cambió)
python manage.py run-scrapers --source adefa
```

Si fallan, es normal. Requieren ajustes según la estructura actual de los sitios.

---

## 🎯 Checklist de Prueba Exitosa

- [ ] `test_setup.py` ejecutado sin errores
- [ ] Base de datos `mercado_automotor` creada
- [ ] 5 tablas creadas en la base de datos
- [ ] Datos de BCRA descargados (ver con `python manage.py stats`)
- [ ] Datos de MercadoLibre descargados
- [ ] Dashboard Streamlit abierto en http://localhost:8501
- [ ] Se ven gráficos en el dashboard
- [ ] API REST funcionando en http://localhost:8000/docs

---

## 🐛 Troubleshooting Común

### Error: "No module named 'backend'"

```bash
# Asegúrate de estar en el directorio correcto
cd c:\Users\juand\OneDrive\Escritorio\Concecionaria\mercado_automotor

# Y que el entorno virtual esté activado
venv\Scripts\activate
```

### Error: "could not connect to server"

PostgreSQL no está corriendo. Inicialo:
- Windows: Buscar "Services" → Iniciar "PostgreSQL"
- O reinstalar PostgreSQL

### Error: "password authentication failed"

La contraseña en `.env` no es correcta. Editá:
```
DATABASE_URL=postgresql://postgres:TU_PASSWORD_CORRECTA@localhost:5432/mercado_automotor
```

### Error: "port 8501 is already in use"

Otro proceso está usando el puerto. Cerralo o usa otro puerto:
```bash
streamlit run frontend/app.py --server.port 8502
```

---

## 📞 ¿Algo Falló?

Si algo no funciona:

1. Copia el error completo
2. Verifica que estés en el directorio correcto
3. Verifica que el entorno virtual esté activado (`(venv)` en el prompt)
4. Verifica que PostgreSQL esté corriendo

---

**¡Buena suerte con las pruebas! 🚀**
