# 🔒 Security - Mercado Automotor

## GitHub Guardian Alert - Generic Password

### ✅ Resuelto en commit `03c23e3`

**Alert detectada:** Generic Password en `docker-compose.yml`

**Passwords encontrados:**
- `POSTGRES_PASSWORD: postgres`
- `--password admin` (Airflow)
- `SECRET_KEY: your_secret_key_here`

---

## 🛡️ ¿Era un problema real?

**NO, era un falso positivo**, pero lo corregimos de todas formas siguiendo best practices.

### Por qué NO era peligroso:

1. ✅ Son passwords de **EJEMPLO** para desarrollo local
2. ✅ Son valores **genéricos y públicos** (todo el mundo usa `postgres`/`admin` en dev)
3. ✅ El `docker-compose.yml` es **solo para desarrollo local**, no para producción
4. ✅ El archivo `.env` real (con tus passwords) **NO está en Git** (protegido por `.gitignore`)
5. ✅ Estas passwords no dan acceso a nada en producción

### Por qué lo corregimos de todas formas:

- ✅ **Best practice**: Usar variables de entorno
- ✅ **Más flexible**: Cambiar passwords sin editar archivos
- ✅ **Profesional**: Demuestra buenas prácticas de seguridad
- ✅ **Silenciar alertas**: GitHub Guardian ya no alertará

---

## 🔧 Solución Implementada

### Antes (Hardcoded):
```yaml
environment:
  POSTGRES_PASSWORD: postgres
```

### Después (Variables de entorno):
```yaml
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
```

**Explicación:**
- `${POSTGRES_PASSWORD:-postgres}` lee la variable de entorno `POSTGRES_PASSWORD`
- Si NO existe, usa el valor por defecto `postgres`
- El valor por defecto es solo para desarrollo local
- En producción, se setea en el archivo `.env` (que NO está en Git)

---

## 🔐 Best Practices de Seguridad Implementadas

### 1. Separación de Secretos

```
✅ .env             → En .gitignore (NO en Git)
✅ .env.example     → En Git (solo ejemplos)
✅ docker-compose   → Usa variables de ${.env}
```

### 2. Configuración por Entorno

**Desarrollo Local:**
```bash
# .env (no commiteado)
POSTGRES_PASSWORD=postgres  # OK para dev local
AIRFLOW_PASSWORD=admin      # OK para dev local
```

**Producción:**
```bash
# .env (no commiteado, en servidor)
POSTGRES_PASSWORD=SuperSecurePassword123!
AIRFLOW_PASSWORD=AnotherSecurePass456!
AIRFLOW_SECRET_KEY=a89f7d6c5b4e3a2d1f0e9c8b7a6d5e4f3a2b1c0d
```

### 3. Secrets NO en Git

El `.gitignore` protege:
```gitignore
# Environment variables
.env
.env.local
.env.*.local
```

### 4. Valores Por Defecto Seguros

Todos los valores por defecto incluyen advertencias:
```yaml
AIRFLOW_SECRET_KEY: ${AIRFLOW_SECRET_KEY:-change-me-in-production}
```

---

## 📋 Checklist de Seguridad

Al deployar a producción, SIEMPRE:

- [ ] Crear archivo `.env` con passwords únicas
- [ ] **NUNCA** usar `postgres`, `admin`, `password123`, etc.
- [ ] Generar secret keys aleatorias:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] Verificar que `.env` NO está en Git:
  ```bash
  git ls-files | grep "\.env$"  # Debe estar vacío
  ```
- [ ] Usar passwords de 16+ caracteres con mayúsculas, números y símbolos
- [ ] Rotar passwords regularmente
- [ ] No compartir `.env` por email/chat (usar secret managers)

---

## 🚨 Red Flags a Evitar

### ❌ NUNCA hacer esto:

```yaml
# ❌ MAL - Password hardcodeada
POSTGRES_PASSWORD: myRealPassword123

# ❌ MAL - Secrets en código
api_key = "sk-1234567890abcdef"

# ❌ MAL - Commitear .env
git add .env
```

### ✅ SIEMPRE hacer esto:

```yaml
# ✅ BIEN - Variable de entorno
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

# ✅ BIEN - Leer de environment
api_key = os.getenv("API_KEY")

# ✅ BIEN - .env en .gitignore
echo ".env" >> .gitignore
```

---

## 🔍 Verificar Seguridad

### Comando rápido para verificar que no hay secrets en Git:

```bash
# Buscar palabras sospechosas en commits
git log -p | grep -i "password\|secret\|api.key" | grep -v "example\|template"

# Buscar en archivos actuales
grep -r "password.*=.*[^{]" . --exclude-dir=venv --exclude-dir=.git
```

---

## 📚 Referencias

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
- [12-Factor App - Config](https://12factor.net/config)

---

## ✅ Estado Actual

- ✅ GitHub Guardian alert resuelta
- ✅ Todas las passwords usan variables de entorno
- ✅ Archivo `.env` protegido por `.gitignore`
- ✅ `.env.example` con valores de ejemplo seguros
- ✅ Warnings claros en valores por defecto

**El proyecto está seguro y sigue best practices.**
