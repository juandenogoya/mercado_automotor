# 🚀 QUICK START - Acceso a MercadoLibre API

## Resumen

Esta guía te lleva paso a paso desde cero hasta tener acceso completo a la API de MercadoLibre para obtener datos del mercado automotor argentino.

**Tiempo estimado:** 30-45 minutos

---

## 📋 Pre-requisitos

✅ Cuenta de MercadoLibre (personal)
✅ Python 3.8+ instalado
✅ Proyecto clonado y dependencias instaladas

---

## 🎯 Pasos Rápidos

### 1. Registrarse como Developer (15 min)

1. **Ir al portal de developers**
   ```
   https://developers.mercadolibre.com.ar/
   ```

2. **Iniciar sesión** con tu cuenta de MercadoLibre

3. **Crear una aplicación**
   - Ir a "Mis Aplicaciones" → "Crear aplicación"
   - Nombre: `Mercado Automotor Analytics`
   - Redirect URI: `http://localhost:8080/callback`
   - Scopes: `read`, `offline_access`

4. **Copiar credenciales**
   - Client ID: `XXXXXXXXXX`
   - Client Secret: `YYYYYYYYYYYY`

📚 **Guía detallada:** `GUIA_REGISTRO_MERCADOLIBRE_DEVELOPER.md`

---

### 2. Configurar Credenciales (5 min)

1. **Crear archivo `.env` en la raíz del proyecto**
   ```bash
   touch .env
   ```

2. **Agregar credenciales al archivo `.env`**
   ```bash
   # MercadoLibre API Credentials
   MERCADOLIBRE_CLIENT_ID=tu_client_id_aqui
   MERCADOLIBRE_CLIENT_SECRET=tu_client_secret_aqui

   # OAuth2 Configuration
   MERCADOLIBRE_REDIRECT_URI=http://localhost:8080/callback
   MERCADOLIBRE_TOKEN_FILE=.meli_tokens.json
   ```

3. **Verificar configuración**
   ```bash
   python backend/auth/verify_credentials.py
   ```

   Deberías ver:
   ```
   ✅ Client ID configurado
   ✅ Client Secret configurado
   ✅ .env está en .gitignore
   ```

---

### 3. Autenticarse con OAuth2 (5 min)

1. **Ejecutar script de autenticación**
   ```bash
   python backend/auth/mercadolibre_oauth.py
   ```

2. **Seguir el flujo OAuth2**
   - Se abrirá una ventana del navegador
   - Iniciar sesión en MercadoLibre si es necesario
   - Autorizar la aplicación "Mercado Automotor Analytics"
   - La ventana mostrará "✅ Autenticación Exitosa"

3. **Verificar tokens guardados**
   ```bash
   ls -la .meli_tokens.json
   ```

   El archivo `.meli_tokens.json` contiene tus tokens (está en `.gitignore`).

---

### 4. Probar Acceso a la API (5 min)

```bash
python test_mercadolibre_authenticated.py
```

Deberías ver:
```
✅ Autenticado correctamente
✅ Búsqueda por marca (Toyota): OK
✅ Búsqueda vehículos 0km: OK
✅ Búsqueda vehículos usados: OK
✅ Detalle de item: OK
✅ Búsqueda con filtros múltiples: OK

🎯 Tests pasados: 5/5
✅ ¡ÉXITO TOTAL!
```

---

## ✅ ¡Listo!

Ya tenés acceso completo a la API de MercadoLibre 🎉

---

## 📊 Uso del Cliente

### Ejemplo básico

```python
from backend.auth.mercadolibre_oauth import MercadoLibreAuth
from backend.api_clients.mercadolibre_client import MercadoLibreClient

# Inicializar autenticación
auth = MercadoLibreAuth()

# Crear cliente con autenticación
client = MercadoLibreClient(auth=auth)

# Buscar vehículos
result = client.search_vehicles(
    marca="Toyota",
    condicion="new",
    limit=50
)

print(f"Total encontrados: {result['total']}")

for item in result['results']:
    print(f"{item['title']} - ${item['price']:,.0f}")
```

### Búsqueda con filtros avanzados

```python
# Buscar Ford Ranger 0km
result = client.search_vehicles(
    marca="Ford",
    modelo="Ranger",
    condicion="new",
    anio_desde=2024,
    limit=50
)
```

### Obtener detalle de un item

```python
# Obtener detalle completo
detail = client.get_item_detail("MLA1234567890")

print(detail['title'])
print(f"Precio: ${detail['price']:,.0f}")
print(f"Atributos: {len(detail['attributes'])}")
```

### Generar snapshot del mercado

```python
# Scrapear mercado completo
result = client.scrape_market_snapshot(
    marcas=["Toyota", "Ford", "Volkswagen"],
    max_items_por_marca=100
)

print(f"Items scraped: {result['items_scraped']}")
print(f"Items guardados: {result['items_saved']}")
```

---

## 🔄 Gestión de Tokens

### Tokens se refrescan automáticamente

El sistema maneja automáticamente:
- ✅ Refresh de tokens expirados
- ✅ Actualización de headers de autenticación
- ✅ Guardado de nuevos tokens

**No necesitás hacer nada manualmente.**

### Si el token expira

Si por alguna razón el token no se puede refrescar:

```bash
# Re-autenticar
python backend/auth/mercadolibre_oauth.py
```

### Borrar tokens y re-autenticar

```bash
# Borrar tokens
rm .meli_tokens.json

# Re-autenticar
python backend/auth/mercadolibre_oauth.py
```

---

## 🚨 Troubleshooting

### Error: "403 Forbidden"

**Causa:** Token expirado o inválido

**Solución:**
```bash
python backend/auth/mercadolibre_oauth.py
```

### Error: "Credenciales no configuradas"

**Causa:** `.env` no existe o está mal configurado

**Solución:**
1. Verificar que `.env` existe
2. Verificar que las credenciales son correctas
3. Ejecutar: `python backend/auth/verify_credentials.py`

### Error: "Invalid redirect_uri"

**Causa:** La URL de redirección no coincide

**Solución:**
1. Verificar en la aplicación de MercadoLibre: `http://localhost:8080/callback`
2. Verificar en `.env`: `MERCADOLIBRE_REDIRECT_URI=http://localhost:8080/callback`
3. Deben ser **exactamente iguales**

### Error: "Rate limit exceeded"

**Causa:** Demasiadas requests en poco tiempo

**Solución:**
- El cliente maneja automáticamente el rate limiting
- Si ves este error, el sistema esperará automáticamente
- Configurar en `.env`: `MERCADOLIBRE_RATE_LIMIT=100` (default)

---

## 🎓 Documentación Adicional

- **Guía de registro:** `GUIA_REGISTRO_MERCADOLIBRE_DEVELOPER.md`
- **Situación de la API:** `MERCADOLIBRE_API_SITUACION.md`
- **Documentación oficial:** https://developers.mercadolibre.com.ar/

---

## 📈 Próximos Pasos

Una vez que tenés acceso a la API, podés:

### 1. Crear scraper automático
```python
# Scrapear diariamente el mercado completo
python scripts/daily_mercadolibre_scraper.py
```

### 2. Análisis de precios
```python
# Analizar evolución de precios
python scripts/analyze_mercadolibre_prices.py
```

### 3. Dashboard interactivo
```bash
# Visualizar datos con Streamlit
streamlit run frontend/mercadolibre_dashboard.py
```

### 4. Comparación con datos oficiales
```python
# Comparar MercadoLibre vs datos.gob.ar
python scripts/compare_mercadolibre_vs_dnrpa.py
```

---

## 💡 Tips y Best Practices

### ✅ DO

- ✅ Respetar rate limits (100 req/min por defecto)
- ✅ Guardar tokens en `.meli_tokens.json` (gitignored)
- ✅ Usar el cliente con autenticación siempre
- ✅ Refrescar tokens automáticamente
- ✅ Cachear resultados cuando sea posible

### ❌ DON'T

- ❌ Subir credenciales a Git
- ❌ Hacer requests directos sin el cliente
- ❌ Exceder rate limits
- ❌ Compartir tokens
- ❌ Hardcodear credenciales en código

---

## 📞 Soporte

Si tenés problemas:

1. Revisar esta guía
2. Revisar `MERCADOLIBRE_API_SITUACION.md`
3. Ejecutar: `python backend/auth/verify_credentials.py`
4. Revisar logs en `logs/app.log`

---

## 🎉 ¡A scrapear!

Ya tenés todo listo para acceder a datos reales del mercado automotor argentino.

**¡Éxito con el proyecto!** 🚗💨
