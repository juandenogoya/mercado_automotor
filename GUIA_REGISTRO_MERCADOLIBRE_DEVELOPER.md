# 🔐 GUÍA: Registro como Developer en MercadoLibre

## Paso 1: Crear Cuenta de Developer

1. **Acceder al portal de developers**
   - URL: https://developers.mercadolibre.com.ar/
   - Click en "Registrate" o "Ingresar"

2. **Iniciar sesión con tu cuenta de MercadoLibre**
   - Usa tu cuenta personal de MercadoLibre
   - Si no tenés cuenta, creá una en https://www.mercadolibre.com.ar/

3. **Completar perfil de developer**
   - Nombre completo
   - Email de contacto
   - País: Argentina

---

## Paso 2: Crear una Aplicación

1. **Ir a "Mis Aplicaciones"**
   - En el portal de developers, ir a la sección "Mis aplicaciones"
   - Click en "Crear aplicación" o "Nueva aplicación"

2. **Completar información de la aplicación**

   **Nombre de la aplicación:**
   ```
   Mercado Automotor Analytics
   ```

   **Descripción corta:**
   ```
   Plataforma de análisis del mercado automotor argentino con datos de MercadoLibre
   ```

   **Descripción larga:**
   ```
   Aplicación de análisis y visualización de datos del mercado automotor argentino.
   Recopila información de listados de vehículos en MercadoLibre para generar
   insights sobre precios, tendencias, oferta y demanda del sector automotor.
   ```

   **Categoría:**
   ```
   Analytics / Data Analysis
   ```

   **URL de redirección (Redirect URI):**
   ```
   http://localhost:8080/callback
   ```

   ⚠️ **IMPORTANTE**: Esta URL debe coincidir exactamente con la configurada en el código.
   Para desarrollo local, usar `http://localhost:8080/callback`

3. **Permisos requeridos (Scopes)**

   Seleccionar los siguientes scopes:
   - ✅ `read` - Leer información pública
   - ✅ `offline_access` - Obtener refresh tokens (para acceso prolongado)

   **NO necesitamos:**
   - ❌ `write` - No vamos a publicar items
   - ❌ `delete` - No vamos a eliminar items

---

## Paso 3: Obtener Credenciales

Una vez creada la aplicación, vas a recibir:

### 🔑 Client ID (App ID)
```
Ejemplo: 1234567890123456
```
Este es tu identificador público de aplicación.

### 🔐 Client Secret
```
Ejemplo: abcdefghijklmnopqrstuvwxyz123456
```
⚠️ **CRÍTICO**: Mantener SECRETO. No compartir ni subir a Git.

---

## Paso 4: Configurar Variables de Entorno

1. **Crear archivo `.env` en la raíz del proyecto**

   ```bash
   cd /home/user/mercado_automotor
   touch .env
   ```

2. **Agregar las credenciales al archivo `.env`**

   ```bash
   # MercadoLibre API Credentials
   MERCADOLIBRE_CLIENT_ID=TU_CLIENT_ID_AQUI
   MERCADOLIBRE_CLIENT_SECRET=TU_CLIENT_SECRET_AQUI

   # OAuth2 Configuration
   MERCADOLIBRE_REDIRECT_URI=http://localhost:8080/callback

   # Token Storage
   MERCADOLIBRE_TOKEN_FILE=.meli_tokens.json
   ```

3. **Verificar que `.env` está en `.gitignore`**

   ```bash
   grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
   grep -q "^\.meli_tokens\.json$" .gitignore || echo ".meli_tokens.json" >> .gitignore
   ```

---

## Paso 5: Verificar Configuración

Ejecutar el script de verificación:

```bash
python backend/auth/verify_credentials.py
```

Debe mostrar:
```
✅ Client ID configurado
✅ Client Secret configurado
✅ Redirect URI configurado
```

---

## 📋 Información de Referencia

### URLs Importantes

- **Portal Developers**: https://developers.mercadolibre.com.ar/
- **Mis Aplicaciones**: https://developers.mercadolibre.com.ar/apps
- **Documentación OAuth**: https://developers.mercadolibre.com.ar/es_ar/autenticacion-y-autorizacion
- **API Reference**: https://developers.mercadolibre.com.ar/es_ar/items-y-busquedas

### Límites de la API

- **Rate Limit**: 100 requests por minuto (por defecto)
- **Access Token**: Válido por 6 horas (21600 segundos)
- **Refresh Token**: Single-use, obtener nuevo con cada refresh

### Troubleshooting

**Problema: "Invalid redirect_uri"**
- Verificar que la URL en el código coincida EXACTAMENTE con la configurada en la app

**Problema: "Invalid client credentials"**
- Verificar que CLIENT_ID y CLIENT_SECRET estén correctos en `.env`
- Verificar que no haya espacios extras al copiar/pegar

**Problema: "Access denied"**
- Verificar que los scopes solicitados coincidan con los autorizados
- Re-autorizar la aplicación si es necesario

---

## ✅ Checklist Final

Antes de continuar con la autenticación, verificar:

- [ ] Cuenta de developer creada
- [ ] Aplicación "Mercado Automotor Analytics" creada
- [ ] Client ID obtenido
- [ ] Client Secret obtenido
- [ ] Archivo `.env` creado con credenciales
- [ ] `.env` agregado a `.gitignore`
- [ ] Redirect URI configurada: `http://localhost:8080/callback`
- [ ] Scopes autorizados: `read`, `offline_access`

---

## 🚀 Próximo Paso

Una vez completados todos los pasos, ejecutar:

```bash
python backend/auth/mercadolibre_oauth.py
```

Esto iniciará el flujo de autenticación OAuth2 y obtendrá el primer access token.
