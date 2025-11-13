"""
Script standalone para analizar todos los datasets disponibles en todas las ramas del proyecto.

Genera:
1. Excel con inventario completo de datasets por rama
2. Markdown con documentación detallada del proyecto

Uso:
    python backend/scripts/analizar_todas_ramas_standalone.py
"""
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
from collections import defaultdict
import os
import sys

root_dir = Path(__file__).parent.parent.parent


def log(message):
    """Simple logging function."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def get_all_branches():
    """Obtiene lista de todas las ramas del repositorio."""
    log("🔍 Obteniendo lista de ramas...")

    result = subprocess.run(
        ["git", "branch", "-a"],
        capture_output=True,
        text=True,
        cwd=root_dir
    )

    branches = []
    for line in result.stdout.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Remover asterisco de rama actual
        if line.startswith('*'):
            line = line[1:].strip()

        # Procesar ramas remotas
        if line.startswith('remotes/origin/'):
            branch_name = line.replace('remotes/origin/', '')
            if branch_name not in ['HEAD', 'main']:
                branches.append(branch_name)
        # Procesar ramas locales (excepto remotes)
        elif not line.startswith('remotes/'):
            branches.append(line)

    # Eliminar duplicados
    branches = list(set(branches))
    branches.sort()

    log(f"✓ Encontradas {len(branches)} ramas")
    return branches


def get_current_branch():
    """Obtiene la rama actual."""
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        cwd=root_dir
    )
    return result.stdout.strip()


def get_files_in_branch(branch_name, pattern):
    """Lista archivos en una rama que coincidan con el patrón."""
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", branch_name],
        capture_output=True,
        text=True,
        cwd=root_dir
    )

    if result.returncode != 0:
        return []

    files = [f for f in result.stdout.split('\n') if pattern in f and f.endswith('.py')]
    return files


def get_models_in_branch(branch_name):
    """Obtiene los modelos disponibles en una rama específica."""
    log(f"  Analizando rama: {branch_name}")

    # Intentar leer el archivo __init__.py de models
    result = subprocess.run(
        ["git", "show", f"{branch_name}:backend/models/__init__.py"],
        capture_output=True,
        text=True,
        cwd=root_dir
    )

    if result.returncode != 0:
        log(f"    No se pudo leer models/__init__.py en {branch_name}")
        return []

    # Parsear imports
    models = []
    for line in result.stdout.split('\n'):
        line = line.strip()
        if line.startswith('from .') and 'import' in line:
            # Extraer nombre del modelo
            parts = line.split('import')
            if len(parts) == 2:
                model_name = parts[1].strip()
                models.append(model_name)

    log(f"    ✓ {len(models)} modelos encontrados")
    return models


def get_scripts_in_branch(branch_name):
    """Obtiene los scripts disponibles en una rama."""
    files = get_files_in_branch(branch_name, 'backend/scripts/')
    return [f.split('/')[-1] for f in files if 'scripts/' in f]


def get_branch_documentation(branch_name):
    """Obtiene archivos de documentación de una rama."""
    log(f"  Buscando documentación en {branch_name}...")

    docs = {}

    # Archivos de documentación a buscar
    doc_files = [
        'README.md',
        'RESUMEN_PROYECTO.md',
        'RESUMEN_SESION.md',
        'ESTADO_PROYECTO.md',
        'DASHBOARD_DATOS_GOB.md',
        'DNRPA_SCRAPER.md',
        'FUENTES_DATOS_INVESTIGACION.md',
        'ANALISIS_MODELOS_Y_DATOS.md',
        'INDICADORES_CALCULADOS.md'
    ]

    for doc_file in doc_files:
        result = subprocess.run(
            ["git", "show", f"{branch_name}:{doc_file}"],
            capture_output=True,
            text=True,
            cwd=root_dir
        )

        if result.returncode == 0:
            # Tomar primeras 10 líneas como resumen
            lines = result.stdout.split('\n')[:10]
            docs[doc_file] = '\n'.join(lines)

    return docs


def get_commit_info(branch_name):
    """Obtiene información del último commit de una rama."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H|%an|%ae|%ci|%s", branch_name],
        capture_output=True,
        text=True,
        cwd=root_dir
    )

    if result.returncode != 0:
        return {}

    parts = result.stdout.strip().split('|')
    if len(parts) >= 5:
        return {
            'hash': parts[0][:8],
            'author': parts[1],
            'email': parts[2],
            'date': parts[3],
            'message': parts[4]
        }
    return {}


def generar_excel_inventario(branches_data, output_file='INVENTARIO_DATASETS_COMPLETO.xlsx'):
    """Genera Excel con inventario completo de datasets."""
    log("=" * 80)
    log("📊 GENERANDO EXCEL DE INVENTARIO")
    log("=" * 80)

    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

            # Hoja 1: Índice de Ramas
            log("\n📋 Hoja 1: Índice de Ramas")
            indice_ramas = []
            for branch_name, data in branches_data.items():
                commit_info = data.get('commit_info', {})
                indice_ramas.append({
                    'Rama': branch_name,
                    'Modelos': len(data['models']),
                    'Scripts': len(data['scripts']),
                    'Documentos': len(data['docs']),
                    'Último Commit': commit_info.get('date', 'N/A')[:10] if commit_info else 'N/A',
                    'Autor': commit_info.get('author', 'N/A') if commit_info else 'N/A',
                    'Mensaje': commit_info.get('message', 'N/A')[:50] if commit_info else 'N/A'
                })

            df_indice = pd.DataFrame(indice_ramas)
            df_indice.to_excel(writer, sheet_name='Índice Ramas', index=False)

            # Hoja 2: Modelos por Rama
            log("\n📊 Hoja 2: Modelos por Rama")
            modelos_por_rama = []
            for branch_name, data in branches_data.items():
                for model in data['models']:
                    modelos_por_rama.append({
                        'Rama': branch_name,
                        'Modelo': model
                    })

            if modelos_por_rama:
                df_modelos = pd.DataFrame(modelos_por_rama)
                df_modelos.to_excel(writer, sheet_name='Modelos', index=False)

            # Hoja 3: Scripts por Rama
            log("\n📜 Hoja 3: Scripts por Rama")
            scripts_por_rama = []
            for branch_name, data in branches_data.items():
                for script in data['scripts']:
                    scripts_por_rama.append({
                        'Rama': branch_name,
                        'Script': script
                    })

            if scripts_por_rama:
                df_scripts = pd.DataFrame(scripts_por_rama)
                df_scripts.to_excel(writer, sheet_name='Scripts', index=False)

            # Hoja 4: Documentación por Rama
            log("\n📚 Hoja 4: Documentación por Rama")
            docs_por_rama = []
            for branch_name, data in branches_data.items():
                for doc_name in data['docs'].keys():
                    docs_por_rama.append({
                        'Rama': branch_name,
                        'Documento': doc_name
                    })

            if docs_por_rama:
                df_docs = pd.DataFrame(docs_por_rama)
                df_docs.to_excel(writer, sheet_name='Documentación', index=False)

            # Hoja 5: Resumen Ejecutivo
            log("\n📈 Hoja 5: Resumen Ejecutivo")
            resumen = pd.DataFrame([
                {'Métrica': 'Total de Ramas', 'Valor': len(branches_data)},
                {'Métrica': 'Modelos Totales', 'Valor': sum(len(d['models']) for d in branches_data.values())},
                {'Métrica': 'Scripts Totales', 'Valor': sum(len(d['scripts']) for d in branches_data.values())},
                {'Métrica': 'Documentos Totales', 'Valor': sum(len(d['docs']) for d in branches_data.values())},
                {'Métrica': 'Fecha de Generación', 'Valor': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                {'Métrica': 'Proyecto', 'Valor': 'Mercado Automotor - Inteligencia Comercial'},
            ])
            resumen.to_excel(writer, sheet_name='Resumen', index=False)

            # Ajustar anchos de columnas
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 80)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        log(f"\n✅ Excel generado: {output_file}")
        return output_file

    except Exception as e:
        log(f"❌ Error generando Excel: {e}")
        raise


def generar_markdown_proyecto(branches_data, output_file='MAPA_COMPLETO_PROYECTO.md'):
    """Genera documentación Markdown completa del proyecto."""
    log("=" * 80)
    log("📝 GENERANDO DOCUMENTACIÓN MARKDOWN")
    log("=" * 80)

    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    md_content = f"""# 🗺️ Mapa Completo del Proyecto - Mercado Automotor

**Fecha de Generación:** {current_date}
**Proyecto:** Sistema de Inteligencia Comercial para el Sector Automotor Argentino

---

## 📋 Índice

1. Resumen Ejecutivo
2. Inventario de Ramas
3. Detalles Completos por Rama
4. Próximos Pasos Recomendados

---

## 🎯 Resumen Ejecutivo

### Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Total de Ramas** | {len(branches_data)} |
| **Total de Modelos (sum)** | {sum(len(d['models']) for d in branches_data.values())} |
| **Total de Scripts (sum)** | {sum(len(d['scripts']) for d in branches_data.values())} |
| **Total de Documentos (sum)** | {sum(len(d['docs']) for d in branches_data.values())} |
| **Fecha de Análisis** | {current_date} |

### Objetivos del Proyecto

- **Sistema de Inteligencia Comercial** para gerencias comerciales del sector automotor
- **Integración de fuentes públicas**: ACARA, ADEFA, BCRA, INDEC, MercadoLibre, datos.gob.ar
- **Análisis predictivo** con ML para anticipar tendencias de mercado
- **Dashboard interactivo** para visualización y exploración de datos
- **Indicadores macro** para medir accesibilidad, volatilidad, tasas reales

---

## 🌿 Inventario de Ramas

El proyecto tiene **{len(branches_data)}** ramas de desarrollo:

| Rama | Modelos | Scripts | Docs | Último Commit | Objetivo Inferido |
|------|---------|---------|------|---------------|-------------------|
"""

    # Agregar ramas
    for branch_name, data in sorted(branches_data.items()):
        objetivo = infer_branch_purpose(branch_name, data)
        commit_info = data.get('commit_info', {})
        commit_date = commit_info.get('date', 'N/A')[:10] if commit_info else 'N/A'

        md_content += f"| `{branch_name}` | {len(data['models'])} | {len(data['scripts'])} | {len(data['docs'])} | {commit_date} | {objetivo} |\n"

    md_content += """

---

## 📚 Detalles Completos por Rama

"""

    # Detalles de cada rama
    for branch_name, data in sorted(branches_data.items()):
        md_content += f"""
### 🌿 Rama: `{branch_name}`

"""

        # Commit info
        commit_info = data.get('commit_info', {})
        if commit_info:
            md_content += f"""**Último Commit:**
- Hash: `{commit_info.get('hash', 'N/A')}`
- Autor: {commit_info.get('author', 'N/A')}
- Fecha: {commit_info.get('date', 'N/A')}
- Mensaje: {commit_info.get('message', 'N/A')}

"""

        # Objetivo
        md_content += f"""**Objetivo:**
{infer_branch_purpose(branch_name, data)}

"""

        # Modelos
        if data['models']:
            md_content += f"""**Modelos Definidos ({len(data['models'])}):**
"""
            for model in sorted(data['models']):
                md_content += f"- `{model}`\n"
            md_content += "\n"

        # Scripts
        if data['scripts']:
            md_content += f"""**Scripts Disponibles ({len(data['scripts'])}):**
"""
            for script in sorted(data['scripts'])[:20]:  # Primeros 20
                md_content += f"- `{script}`\n"

            if len(data['scripts']) > 20:
                md_content += f"- ... y {len(data['scripts']) - 20} más\n"
            md_content += "\n"

        # Documentación
        if data['docs']:
            md_content += f"""**Documentación ({len(data['docs'])}):**
"""
            for doc_file in sorted(data['docs'].keys()):
                md_content += f"- `{doc_file}`\n"
            md_content += "\n"

        md_content += "---\n"

    md_content += """

## 🚀 Próximos Pasos Recomendados

### Para Comenzar una Nueva Sesión

1. **Revisar este documento** (`MAPA_COMPLETO_PROYECTO.md`) para entender el estado actual
2. **Verificar el Excel** (`INVENTARIO_DATASETS_COMPLETO.xlsx`) para conocer datasets disponibles
3. **Consultar rama específica** según el objetivo:
   - Para indicadores macro → `claude/review-project-summary-*`
   - Para datos.gob.ar dashboard → `claude/continue-project-*`
   - Para datos DNRPA completos (13.6M) → `claude/review-project-advantages-*`

### Comandos Útiles para Cambiar de Rama

```bash
# Ver todas las ramas
git branch -a

# Cambiar a una rama específica
git checkout <nombre-rama>

# Crear rama local tracking desde remote
git checkout -b <nombre-rama> origin/<nombre-rama>

# Ver diferencias entre ramas
git diff <rama1>..<rama2>
```

### Tareas Pendientes Identificadas

- [ ] Unificar datasets de todas las ramas en una sola
- [ ] Integrar modelos de datos.gob.ar (Inscripciones, Transferencias, Prendas)
- [ ] Completar carga de datos históricos
- [ ] Entrenar y validar modelos de ML
- [ ] Desarrollar dashboard unificado

---

## 📞 Información Adicional

**Stack Tecnológico:**
- Python 3.11+
- PostgreSQL 15 + TimescaleDB
- FastAPI (API REST)
- Streamlit (Dashboards)
- SQLAlchemy (ORM)
- Pandas, NumPy (Análisis)
- Scikit-learn, XGBoost, Prophet (ML)

**Fuentes de Datos Integradas:**
- ACARA (patentamientos)
- ADEFA (producción)
- BCRA (tasas, indicadores económicos)
- INDEC (IPC, inflación)
- MercadoLibre (precios de mercado)
- datos.gob.ar - DNRPA (inscripciones, transferencias, prendas)

---

**Generado automáticamente por:** `backend/scripts/analizar_todas_ramas_standalone.py`
**Fecha:** {current_date}
"""

    # Escribir archivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    log(f"\n✅ Markdown generado: {output_file}")
    return output_file


def infer_branch_purpose(branch_name, data):
    """Infiere el propósito de una rama basándose en su nombre y contenido."""
    name_lower = branch_name.lower()

    if 'summary' in name_lower:
        return 'Revisión y resumen del proyecto. Cálculo de indicadores macroeconómicos (IPC, BADLAR, TC).'
    elif 'advantages' in name_lower:
        return 'Exploración de ventajas competitivas. Integración de datos.gob.ar DNRPA (13.6M registros: Inscripciones, Transferencias, Prendas).'
    elif 'continue' in name_lower:
        return 'Continuación del proyecto. Dashboard interactivo datos.gob.ar con análisis YoY y MoM. Entrenamiento de modelos ML.'
    elif 'dashboard' in name_lower and 'detallado' in name_lower:
        return 'Dashboard de análisis detallado.'
    elif 'dashboard' in name_lower and 'sync' in name_lower:
        return 'Sincronización de dashboard.'
    elif 'fix' in name_lower:
        return 'Corrección de bugs y problemas técnicos.'
    elif 'desarrollo' in name_lower:
        return 'Rama principal de desarrollo. Dashboard datos.gob.ar 2025.'
    elif name_lower == 'main':
        return 'Rama principal del proyecto.'
    else:
        # Inferir por documentación disponible
        docs = data.get('docs', {})
        if 'DNRPA_SCRAPER.md' in docs:
            return 'Rama con scraper DNRPA y datos masivos de automotores.'
        elif 'DASHBOARD_DATOS_GOB.md' in docs:
            return 'Rama con dashboard de análisis datos.gob.ar.'
        elif 'INDICADORES_CALCULADOS.md' in docs:
            return 'Rama con cálculo de indicadores macroeconómicos.'
        else:
            return 'Rama de desarrollo del proyecto.'


def main():
    """Función principal."""
    log("=" * 80)
    log("🗺️  ANÁLISIS COMPLETO DEL PROYECTO")
    log("=" * 80)
    log("\nEste script analiza:")
    log("  1. Todas las ramas del repositorio Git")
    log("  2. Modelos definidos en cada rama")
    log("  3. Scripts disponibles en cada rama")
    log("  4. Documentación disponible en cada rama")
    log("  5. Genera Excel + Markdown con inventario completo")
    log("")

    # Guardar rama actual
    current_branch = get_current_branch()
    log(f"Rama actual: {current_branch}")

    # Paso 1: Obtener todas las ramas
    branches = get_all_branches()

    # Paso 2: Analizar cada rama
    log("\n" + "=" * 80)
    log("ANALIZANDO RAMAS")
    log("=" * 80)

    branches_data = {}
    for branch in branches:
        models = get_models_in_branch(branch)
        scripts = get_scripts_in_branch(branch)
        docs = get_branch_documentation(branch)
        commit_info = get_commit_info(branch)

        branches_data[branch] = {
            'models': models,
            'scripts': scripts,
            'docs': docs,
            'commit_info': commit_info
        }

    # Paso 3: Generar Excel
    log("\n" + "=" * 80)
    log("GENERANDO ARCHIVOS")
    log("=" * 80)

    excel_file = generar_excel_inventario(branches_data)

    # Paso 4: Generar Markdown
    md_file = generar_markdown_proyecto(branches_data)

    # Resumen final
    log("\n" + "=" * 80)
    log("✅ ANÁLISIS COMPLETADO")
    log("=" * 80)
    log(f"\n📊 Archivos generados:")
    log(f"  1. Excel: {excel_file}")
    log(f"  2. Markdown: {md_file}")
    log(f"\n📈 Estadísticas:")
    log(f"  Ramas analizadas: {len(branches_data)}")
    log(f"  Modelos totales: {sum(len(d['models']) for d in branches_data.values())}")
    log(f"  Scripts totales: {sum(len(d['scripts']) for d in branches_data.values())}")
    log(f"  Documentos totales: {sum(len(d['docs']) for d in branches_data.values())}")
    log("\n💡 Próximos pasos:")
    log(f"  - Revisa el Excel para ver inventario completo")
    log(f"  - Lee el Markdown para documentación detallada")
    log(f"  - Usa estos archivos para comenzar futuras sesiones")
    log("=" * 80)


if __name__ == "__main__":
    main()
