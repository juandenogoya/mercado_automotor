# 📤 Instrucciones para Subir a GitHub

## ✅ Estado Actual del Proyecto

- ✅ Repositorio Git inicializado
- ✅ Commit inicial realizado (39 archivos, 5,800 líneas)
- ✅ Fix de compatibilidad SQLAlchemy commiteado
- ✅ Entorno virtual Python creado
- ⏳ Instalando dependencias en segundo plano...

## 🚀 Pasos para Subir a GitHub

### 1. Crear Repositorio en GitHub

1. Ve a https://github.com/new
2. Configuración recomendada:
   - **Repository name**: `mercado-automotor`
   - **Description**: `Sistema de Inteligencia Comercial del Mercado Automotor Argentino - MVP`
   - **Visibility**: Private (o Public según tu preferencia)
   - **⚠️ NO inicialices con README** (ya tenemos uno)
   - **⚠️ NO agregues .gitignore** (ya tenemos uno)
   - **⚠️ NO agregues licencia** (puedes hacerlo después)
3. Click en "Create repository"

### 2. Conectar Repositorio Local con GitHub

Una vez creado el repositorio, GitHub te mostrará instrucciones. Usa estas:

```bash
# Navegar al directorio del proyecto (si no estás ahí)
cd c:\Users\juand\OneDrive\Escritorio\Concecionaria\mercado_automotor

# Agregar remote origin (reemplaza TU-USUARIO con tu usuario de GitHub)
git remote add origin https://github.com/TU-USUARIO/mercado-automotor.git

# Renombrar branch a main (opcional, si prefieres main en vez de master)
git branch -M main

# Push inicial
git push -u origin main
```

### 3. Alternativa: Usar SSH (Recomendado)

Si ya tienes configurado SSH en GitHub:

```bash
# Agregar remote con SSH
git remote add origin git@github.com:TU-USUARIO/mercado-automotor.git

# Push
git branch -M main
git push -u origin main
```

### 4. Verificar que se subió correctamente

1. Ve a tu repositorio en GitHub
2. Deberías ver:
   - ✅ 39 archivos
   - ✅ 2 commits
   - ✅ README.md visualizado en la página principal
   - ✅ Estructura de carpetas completa

## 📋 Commits Actuales

```
* 890eeb6 - fix: ajustar versión de SQLAlchemy para compatibilidad con Airflow 2.7.3
* 53023e3 - Initial commit: MVP Sistema de Inteligencia Comercial - Mercado Automotor
```

## 🔐 Importante: Antes de hacer PUBLIC

Si planeas hacer el repositorio público, asegúrate de:

1. **Revisar .gitignore** - Ya está configurado correctamente
2. **No commitear .env** - Solo .env.example (✅ ya hecho)
3. **No commitear credenciales** - Ninguna incluida (✅ seguro)
4. **Revisar comentarios sensibles** - Todo limpio (✅)

## 📝 Siguientes Pasos Después del Push

### Configurar GitHub Repository Settings

1. **About** (esquina superior derecha):
   - Description: "Sistema de Inteligencia Comercial del Mercado Automotor Argentino"
   - Website: (opcional)
   - Topics: `python`, `fastapi`, `streamlit`, `airflow`, `postgresql`, `data-analysis`, `argentina`, `automotive`

2. **Branch Protection** (opcional pero recomendado):
   - Settings → Branches → Add rule
   - Branch name pattern: `main`
   - ✓ Require pull request reviews before merging
   - ✓ Require status checks to pass

3. **README Badges** (opcional):
   Puedes agregar badges al README.md:
   ```markdown
   ![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
   ![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
   ![License](https://img.shields.io/badge/license-Private-red.svg)
   ```

### Crear GitHub Actions (CI/CD) - Futuro

Archivo `.github/workflows/ci.yml` para tests automáticos:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/
```

## 🆘 Troubleshooting

### Error: "remote origin already exists"

```bash
# Ver remotes actuales
git remote -v

# Eliminar remote existente
git remote remove origin

# Agregar nuevamente
git remote add origin https://github.com/TU-USUARIO/mercado-automotor.git
```

### Error: "Authentication failed"

Si usas HTTPS y falla la autenticación:
1. Genera un Personal Access Token en GitHub
2. Settings → Developer settings → Personal access tokens → Tokens (classic)
3. Generate new token con permisos de `repo`
4. Usa el token como password cuando hagas push

### Push Rechazado

```bash
# Si el remoto tiene commits que no tienes localmente
git pull origin main --rebase

# Luego push
git push -u origin main
```

## ✅ Checklist Final

Antes de considerar el proyecto "subido":

- [ ] Repositorio creado en GitHub
- [ ] Remote origin configurado
- [ ] Push exitoso (`git push -u origin main`)
- [ ] README.md se visualiza correctamente en GitHub
- [ ] Estructura de carpetas visible
- [ ] .env.example visible (pero NO .env)
- [ ] About section configurada
- [ ] Topics agregados

---

**Nota**: Una vez que hagas el push inicial, todos los futuros commits serán más simples:

```bash
# Workflow normal
git add .
git commit -m "Tu mensaje de commit"
git push
```
