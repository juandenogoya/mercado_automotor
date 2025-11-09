# 🚨 MERCADOLIBRE API - SITUACIÓN ACTUAL (2025)

## ❌ Problema Identificado

**TODOS los endpoints de MercadoLibre API retornan error 403 (Forbidden)**

### Tests Realizados:

✅ **Test 1: Cliente existente** (`backend/api_clients/mercadolibre_client.py`)
- ❌ Búsqueda por marca: FAIL (403)
- ❌ Búsqueda 0km: FAIL (403)
- ❌ Búsqueda usados: FAIL (403)

✅ **Test 2: Endpoints públicos**
- ❌ Información del sitio: 403
- ❌ Categorías: 403
- ❌ Búsquedas: 403
- ❌ Items individuales: 403
- ❌ Monedas: 403
- ❌ Tendencias: 403

**Resultado: 0/11 endpoints accesibles sin autenticación**

---

## 🔍 Investigación - Cambios en 2025

### ⚠️ CAMBIO CRÍTICO - Abril 2025

**MercadoLibre cerró el acceso público a su API**

Desde abril 2025, MercadoLibre implementó una política restrictiva:
- **Antes**: Endpoints de búsqueda eran públicos (sin autenticación)
- **Ahora**: TODOS los endpoints requieren autenticación OAuth2

**Fuente**:
- https://www.automatizapro.com.ar/blog/cambios-api-mercado-libre-2025/
- https://developers.mercadolibre.com.ar/

---

## 🔐 Autenticación Requerida - OAuth2

### Proceso para acceder a la API:

1. **Registrar aplicación en MercadoLibre Developers**
   - URL: https://developers.mercadolibre.com.ar/
   - Obtener `Client ID` y `Client Secret`
   - Configurar URL de redirección

2. **Implementar flujo OAuth2**
   ```
   Step 1: Authorization Request
   https://auth.mercadolibre.com.ar/authorization?
     response_type=code&
     client_id=$APP_ID&
     redirect_uri=$YOUR_URL&
     code_challenge=$CODE_CHALLENGE&
     code_challenge_method=$CODE_METHOD

   Step 2: Exchange Code for Token
   POST https://api.mercadolibre.com/oauth/token
   {
     "grant_type": "authorization_code",
     "client_id": "...",
     "client_secret": "...",
     "code": "...",
     "redirect_uri": "...",
     "code_verifier": "..."
   }

   Step 3: Use Access Token
   Authorization: Bearer APP_USR-12345678-031820-X-12345678
   ```

3. **Gestión de tokens**
   - Access Token: válido 6 horas
   - Refresh Token: single-use, obtener nuevo con cada refresh
   - Tokens inválidos si: usuario cambia password, app renueva secret, usuario revoca permisos

---

## 📊 OPCIONES DISPONIBLES

### Opción 1: ✅ **Implementar OAuth2 + MercadoLibre API**

**Ventajas:**
- ✅ Acceso oficial a la API
- ✅ Datos estructurados y completos
- ✅ Rate limits claros
- ✅ Mantenible a largo plazo

**Desventajas:**
- ❌ Requiere registro como developer
- ❌ Proceso de autorización OAuth2 complejo
- ❌ Requiere servidor web para callback
- ❌ Tokens expiran cada 6 horas

**Complejidad:** 🔴 Alta
**Tiempo estimado:** 2-4 horas
**Recomendado para:** Aplicación productiva de largo plazo

**Pasos a seguir:**
1. Registrarse en https://developers.mercadolibre.com.ar/
2. Crear aplicación y obtener credenciales
3. Implementar módulo de autenticación OAuth2
4. Integrar con cliente existente
5. Implementar refresh automático de tokens

---

### Opción 2: 🌐 **Web Scraping de MercadoLibre.com.ar**

**Ventajas:**
- ✅ No requiere credenciales
- ✅ Acceso inmediato
- ✅ Datos públicos disponibles
- ✅ Control total sobre qué datos extraer

**Desventajas:**
- ❌ Puede violar términos de servicio
- ❌ Estructura HTML puede cambiar
- ❌ Requiere rotating proxies / user-agents
- ❌ Rate limiting manual (riesgo de bloqueo IP)
- ❌ Datos menos estructurados

**Complejidad:** 🟡 Media
**Tiempo estimado:** 4-6 horas
**Recomendado para:** Prototipo rápido, análisis puntual

**Tecnologías:**
- BeautifulSoup / Scrapy
- Selenium (para contenido dinámico)
- Rotating proxies
- Headers randomization

---

### Opción 3: 📊 **Usar datos existentes de datos.gob.ar**

**Ventajas:**
- ✅ Ya tenemos 13.6M registros cargados
- ✅ Datos oficiales DNRPA
- ✅ Sin restricciones de API
- ✅ Datos históricos 2019-2025
- ✅ Cobertura completa del mercado

**Desventajas:**
- ❌ No tiene precios de mercado
- ❌ No tiene oferta actual (listings)
- ❌ Datos oficiales vs datos de marketplace

**Complejidad:** 🟢 Baja (ya implementado)
**Tiempo estimado:** 0 horas (listo para usar)
**Recomendado para:** Análisis de patentamientos y mercado oficial

**Datos disponibles:**
- ✅ 2.9M inscripciones (0km)
- ✅ 8.8M transferencias (usados)
- ✅ 1.7M prendas
- ✅ 1,561 registros seccionales

---

### Opción 4: 🔄 **Enfoque Híbrido**

**Combinar múltiples fuentes:**
- 📊 datos.gob.ar → Estadísticas oficiales, patentamientos
- 🌐 Web scraping ML → Precios de mercado actual
- 🏦 BCRA API → Datos económicos (dólar, inflación)

**Ventajas:**
- ✅ Vista completa del mercado
- ✅ Datos oficiales + datos de mercado
- ✅ Redundancia de fuentes

**Desventajas:**
- ❌ Mayor complejidad de integración
- ❌ Múltiples puntos de fallo

**Complejidad:** 🔴 Alta
**Tiempo estimado:** 6-10 horas
**Recomendado para:** Plataforma analítica completa

---

## 🎯 RECOMENDACIÓN

### Para desarrollo inmediato (próximas horas):

**→ Opción 3: Usar datos.gob.ar**

Razones:
1. Ya está implementado y funcionando
2. 13.6M registros oficiales disponibles
3. No hay restricciones de API
4. Permite avanzar con análisis y visualizaciones

### Para desarrollo a mediano plazo (próximos días):

**→ Opción 1: Implementar OAuth2 + API oficial**

Razones:
1. Solución sostenible a largo plazo
2. Acceso a precios de mercado
3. Datos estructurados y completos
4. Cumple con términos de servicio

---

## 📋 PRÓXIMOS PASOS SEGÚN OPCIÓN ELEGIDA

### Si eliges Opción 1 (OAuth2 + API):
1. ✅ Crear cuenta en MercadoLibre Developers
2. ✅ Registrar aplicación
3. ✅ Implementar módulo OAuth2
4. ✅ Integrar con cliente existente
5. ✅ Probar autenticación y búsquedas

### Si eliges Opción 2 (Web Scraping):
1. ✅ Diseñar estrategia de scraping
2. ✅ Implementar scraper con Selenium/BeautifulSoup
3. ✅ Configurar proxies y rate limiting
4. ✅ Crear parser de datos
5. ✅ Guardar en base de datos

### Si eliges Opción 3 (datos.gob.ar):
1. ✅ Crear visualizaciones con Streamlit
2. ✅ Implementar análisis estadísticos
3. ✅ Generar reportes automáticos
4. ✅ Crear dashboard interactivo

### Si eliges Opción 4 (Híbrido):
1. ✅ Comenzar con datos.gob.ar (inmediato)
2. ✅ Implementar scraping ML para precios (corto plazo)
3. ✅ Integrar BCRA API (corto plazo)
4. ✅ Implementar OAuth2 ML (mediano plazo)

---

## 📚 Referencias

- **MercadoLibre Developers**: https://developers.mercadolibre.com.ar/
- **OAuth2 Documentation**: https://developers.mercadolibre.com.ar/es_ar/autenticacion-y-autorizacion
- **Items & Searches API**: https://developers.mercadolibre.com.ar/en_us/items-and-searches
- **Cambios 2025**: https://www.automatizapro.com.ar/blog/cambios-api-mercado-libre-2025/

---

## 💬 Decisión Necesaria

**¿Qué opción prefieres para continuar?**

1. OAuth2 + API oficial (largo plazo, completo)
2. Web scraping (rápido, menos robusto)
3. datos.gob.ar (inmediato, datos oficiales)
4. Híbrido (completo, complejo)

Una vez decidas, podemos proceder con la implementación.
