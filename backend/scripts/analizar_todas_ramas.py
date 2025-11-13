"""
Script para analizar todos los datasets disponibles en todas las ramas del proyecto.

Genera:
1. Excel con inventario completo de datasets por rama
2. Markdown con documentación detallada del proyecto

Uso:
    python backend/scripts/analizar_todas_ramas.py
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
from collections import defaultdict

root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from loguru import logger
from backend.config.logger import setup_logger
from backend.utils.database import get_db, engine
from sqlalchemy import inspect, text


def get_all_branches():
    """Obtiene lista de todas las ramas del repositorio."""
    logger.info("🔍 Obteniendo lista de ramas...")

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

    logger.success(f"✓ Encontradas {len(branches)} ramas")
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


def get_models_in_branch(branch_name):
    """Obtiene los modelos disponibles en una rama específica."""
    logger.info(f"  Analizando rama: {branch_name}")

    # Intentar leer el archivo __init__.py de models
    result = subprocess.run(
        ["git", "show", f"{branch_name}:backend/models/__init__.py"],
        capture_output=True,
        text=True,
        cwd=root_dir
    )

    if result.returncode != 0:
        logger.warning(f"    No se pudo leer models/__init__.py en {branch_name}")
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

    logger.info(f"    ✓ {len(models)} modelos encontrados")
    return models


def get_tables_in_database():
    """Obtiene todas las tablas en la base de datos PostgreSQL."""
    logger.info("🗄️  Consultando base de datos PostgreSQL...")

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        tables_info = []
        with get_db() as db:
            for table in tables:
                # Obtener conteo de registros
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                except:
                    count = 0

                # Obtener columnas
                columns = inspector.get_columns(table)

                tables_info.append({
                    'tabla': table,
                    'registros': count,
                    'columnas': len(columns),
                    'columnas_nombres': [col['name'] for col in columns]
                })

        logger.success(f"✓ {len(tables_info)} tablas encontradas en PostgreSQL")
        return tables_info

    except Exception as e:
        logger.error(f"❌ Error consultando base de datos: {e}")
        return []


def get_branch_documentation(branch_name):
    """Obtiene archivos de documentación de una rama."""
    logger.info(f"  Buscando documentación en {branch_name}...")

    docs = {}

    # Archivos de documentación a buscar
    doc_files = [
        'README.md',
        'RESUMEN_PROYECTO.md',
        'RESUMEN_SESION.md',
        'ESTADO_PROYECTO.md',
        'DASHBOARD_DATOS_GOB.md',
        'DNRPA_SCRAPER.md',
        'FUENTES_DATOS_INVESTIGACION.md'
    ]

    for doc_file in doc_files:
        result = subprocess.run(
            ["git", "show", f"{branch_name}:{doc_file}"],
            capture_output=True,
            text=True,
            cwd=root_dir
        )

        if result.returncode == 0:
            # Tomar primeras 20 líneas como resumen
            lines = result.stdout.split('\n')[:20]
            docs[doc_file] = '\n'.join(lines)

    return docs


def generar_excel_inventario(branches_data, tables_data, output_file='INVENTARIO_DATASETS_COMPLETO.xlsx'):
    """Genera Excel con inventario completo de datasets."""
    logger.info("=" * 80)
    logger.info("📊 GENERANDO EXCEL DE INVENTARIO")
    logger.info("=" * 80)

    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

            # Hoja 1: Índice de Ramas
            logger.info("\n📋 Hoja 1: Índice de Ramas")
            indice_ramas = []
            for branch_name, data in branches_data.items():
                indice_ramas.append({
                    'Rama': branch_name,
                    'Modelos Definidos': len(data['models']),
                    'Tiene Documentación': 'Sí' if data['docs'] else 'No',
                    'Archivos Documentación': ', '.join(data['docs'].keys()) if data['docs'] else '-'
                })

            df_indice = pd.DataFrame(indice_ramas)
            df_indice.to_excel(writer, sheet_name='📋 Índice Ramas', index=False)

            # Hoja 2: Tablas PostgreSQL (Estado Actual)
            logger.info("\n🗄️  Hoja 2: Estado PostgreSQL")
            pg_data = []
            for table in tables_data:
                pg_data.append({
                    'Tabla': table['tabla'],
                    'Registros': f"{table['registros']:,}",
                    'Columnas': table['columnas'],
                    'Columnas (nombres)': ', '.join(table['columnas_nombres'][:10])  # Primeras 10
                })

            df_pg = pd.DataFrame(pg_data)
            df_pg.to_excel(writer, sheet_name='🗄️ PostgreSQL Actual', index=False)

            # Hoja 3: Modelos por Rama
            logger.info("\n📊 Hoja 3: Modelos por Rama")
            modelos_por_rama = []
            for branch_name, data in branches_data.items():
                for model in data['models']:
                    modelos_por_rama.append({
                        'Rama': branch_name,
                        'Modelo': model
                    })

            if modelos_por_rama:
                df_modelos = pd.DataFrame(modelos_por_rama)
                df_modelos.to_excel(writer, sheet_name='📊 Modelos por Rama', index=False)

            # Hoja 4: Resumen Ejecutivo
            logger.info("\n📈 Hoja 4: Resumen Ejecutivo")
            resumen = pd.DataFrame([
                {'Métrica': 'Total de Ramas', 'Valor': len(branches_data)},
                {'Métrica': 'Total de Tablas en PostgreSQL', 'Valor': len(tables_data)},
                {'Métrica': 'Total de Registros en PostgreSQL', 'Valor': f"{sum(t['registros'] for t in tables_data):,}"},
                {'Métrica': 'Fecha de Generación', 'Valor': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                {'Métrica': 'Proyecto', 'Valor': 'Mercado Automotor - Inteligencia Comercial'},
            ])
            resumen.to_excel(writer, sheet_name='📈 Resumen Ejecutivo', index=False)

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

        logger.success(f"\n✅ Excel generado: {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"❌ Error generando Excel: {e}")
        raise


def generar_markdown_proyecto(branches_data, tables_data, output_file='MAPA_COMPLETO_PROYECTO.md'):
    """Genera documentación Markdown completa del proyecto."""
    logger.info("=" * 80)
    logger.info("📝 GENERANDO DOCUMENTACIÓN MARKDOWN")
    logger.info("=" * 80)

    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    md_content = f"""# 🗺️ Mapa Completo del Proyecto - Mercado Automotor

**Fecha de Generación:** {current_date}
**Proyecto:** Sistema de Inteligencia Comercial para el Sector Automotor Argentino

---

## 📋 Índice

1. Resumen Ejecutivo
2. Estado de la Base de Datos PostgreSQL
3. Inventario de Ramas
4. Detalles por Rama
5. Datasets Disponibles
6. Próximos Pasos Recomendados

---

## 🎯 Resumen Ejecutivo

### Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Total de Ramas** | {len(branches_data)} |
| **Total de Tablas en PostgreSQL** | {len(tables_data)} |
| **Total de Registros en PostgreSQL** | {sum(t['registros'] for t in tables_data):,} |
| **Fecha de Último Análisis** | {current_date} |

### Objetivos del Proyecto

- **Sistema de Inteligencia Comercial** para gerencias comerciales del sector automotor
- **Integración de fuentes públicas**: ACARA, ADEFA, BCRA, INDEC, MercadoLibre, datos.gob.ar
- **Análisis predictivo** con ML para anticipar tendencias de mercado
- **Dashboard interactivo** para visualización y exploración de datos
- **Indicadores macro** para medir accesibilidad, volatilidad, tasas reales

---

## 🗄️ Estado de la Base de Datos PostgreSQL

### Tablas Activas

La base de datos actualmente contiene **{len(tables_data)}** tablas:

| Tabla | Registros | Columnas | Descripción |
|-------|-----------|----------|-------------|
"""

    # Agregar tablas
    for table in sorted(tables_data, key=lambda x: x['registros'], reverse=True):
        descripcion = get_table_description(table['tabla'])
        md_content += f"| `{table['tabla']}` | {table['registros']:,} | {table['columnas']} | {descripcion} |\n"

    md_content += f"""
### Total de Registros por Tipo

"""

    # Agrupar por tipo
    totales_por_tipo = defaultdict(int)
    for table in tables_data:
        tipo = classify_table_type(table['tabla'])
        totales_por_tipo[tipo] += table['registros']

    for tipo, total in sorted(totales_por_tipo.items(), key=lambda x: x[1], reverse=True):
        md_content += f"- **{tipo}**: {total:,} registros\n"

    md_content += f"""

---

## 🌿 Inventario de Ramas

El proyecto tiene **{len(branches_data)}** ramas de desarrollo:

| Rama | Modelos | Documentación | Objetivo |
|------|---------|---------------|----------|
"""

    # Agregar ramas
    for branch_name, data in sorted(branches_data.items()):
        objetivo = infer_branch_purpose(branch_name, data)
        docs_list = ', '.join(data['docs'].keys()) if data['docs'] else '-'
        md_content += f"| `{branch_name}` | {len(data['models'])} | {docs_list} | {objetivo} |\n"

    md_content += """

---

## 📚 Detalles por Rama

"""

    # Detalles de cada rama
    for branch_name, data in sorted(branches_data.items()):
        md_content += f"""
### 🌿 Rama: `{branch_name}`

**Modelos Definidos:** {len(data['models'])}

"""
        if data['models']:
            md_content += "**Lista de Modelos:**\n"
            for model in sorted(data['models']):
                md_content += f"- `{model}`\n"

        if data['docs']:
            md_content += f"\n**Documentación Disponible:**\n"
            for doc_file in sorted(data['docs'].keys()):
                md_content += f"- `{doc_file}`\n"

        md_content += f"\n**Objetivo de la Rama:**\n{infer_branch_purpose(branch_name, data)}\n"
        md_content += "\n---\n"

    md_content += """

## 📊 Datasets Disponibles

### Datasets en PostgreSQL (Actual)

"""

    for table in sorted(tables_data, key=lambda x: x['tabla']):
        md_content += f"""
#### `{table['tabla']}`

- **Registros:** {table['registros']:,}
- **Columnas:** {table['columnas']}
- **Columnas Disponibles:**
"""
        for col_name in table['columnas_nombres'][:20]:  # Primeras 20
            md_content += f"  - `{col_name}`\n"

        if len(table['columnas_nombres']) > 20:
            md_content += f"  - ... y {len(table['columnas_nombres']) - 20} más\n"

        md_content += "\n"

    md_content += """

---

## 🚀 Próximos Pasos Recomendados

### Para Comenzar una Nueva Sesión

1. **Revisar este documento** (`MAPA_COMPLETO_PROYECTO.md`) para entender el estado actual
2. **Verificar el Excel** (`INVENTARIO_DATASETS_COMPLETO.xlsx`) para conocer datasets disponibles
3. **Consultar rama específica** según el objetivo:
   - Para indicadores macro → `claude/review-project-summary-*`
   - Para datos.gob.ar → `claude/continue-project-*`
   - Para datos DNRPA completos → `claude/review-project-advantages-*`

### Tareas Pendientes Identificadas

- [ ] Integrar datasets de automotores (Inscripciones, Transferencias, Prendas) desde rama advantages
- [ ] Completar carga de datos históricos en todas las fuentes
- [ ] Entrenar y validar modelos de ML con datos completos
- [ ] Unificar indicadores calculados entre ramas
- [ ] Desarrollar dashboard unificado que integre todas las fuentes

### Comandos Útiles

```bash
# Ver estadísticas actuales
python manage.py stats

# Generar diccionario de datos
python backend/scripts/generar_diccionario_datos.py

# Calcular indicadores macro
python manage.py calcular-indicadores --export-excel indicadores_macro.xlsx

# Iniciar dashboard
streamlit run frontend/app.py
```

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

**Fuentes de Datos:**
- ACARA (patentamientos)
- ADEFA (producción)
- BCRA (tasas, indicadores económicos)
- INDEC (IPC, inflación)
- MercadoLibre (precios de mercado)
- datos.gob.ar - DNRPA (inscripciones, transferencias, prendas)

---

**Generado automáticamente por:** `backend/scripts/analizar_todas_ramas.py`
**Fecha:** {current_date}
"""

    # Escribir archivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    logger.success(f"\n✅ Markdown generado: {output_file}")
    return output_file


def classify_table_type(table_name):
    """Clasifica una tabla según su tipo."""
    if 'ipc' in table_name.lower():
        return 'IPC / Inflación'
    elif 'badlar' in table_name.lower():
        return 'BADLAR / Tasas'
    elif 'tipo_cambio' in table_name.lower() or 'tc_' in table_name.lower():
        return 'Tipo de Cambio'
    elif 'indicador' in table_name.lower():
        return 'Indicadores Calculados'
    elif 'patentamiento' in table_name.lower():
        return 'Patentamientos'
    elif 'produccion' in table_name.lower():
        return 'Producción'
    elif 'inscripc' in table_name.lower():
        return 'Inscripciones (datos.gob.ar)'
    elif 'transferencia' in table_name.lower():
        return 'Transferencias (datos.gob.ar)'
    elif 'prenda' in table_name.lower():
        return 'Prendas (datos.gob.ar)'
    elif 'registro' in table_name.lower() and 'seccional' in table_name.lower():
        return 'Registros Seccionales'
    elif 'bcra' in table_name.lower():
        return 'BCRA'
    elif 'mercadolibre' in table_name.lower() or 'ml_' in table_name.lower():
        return 'MercadoLibre'
    else:
        return 'Otros'


def get_table_description(table_name):
    """Retorna descripción de una tabla."""
    descriptions = {
        'ipc': 'Índice de Precios al Consumidor mensual',
        'ipc_diario': 'IPC expandido a nivel diario',
        'badlar': 'Tasa BADLAR',
        'tipo_cambio': 'Tipo de cambio oficial',
        'indicadores_calculados': 'Indicadores macro calculados (Tasa Real, TCR, etc.)',
        'patentamientos': 'Patentamientos por marca y modelo',
        'produccion': 'Producción de vehículos',
        'bcra_indicadores': 'Indicadores económicos BCRA',
        'mercadolibre_listings': 'Listados de vehículos en MercadoLibre',
        'datos_gob_inscripciones': 'Inscripciones DNRPA (patentamientos 0km)',
        'datos_gob_transferencias': 'Transferencias DNRPA (vehículos usados)',
        'datos_gob_prendas': 'Prendas DNRPA (vehículos financiados)',
        'datos_gob_registros_seccionales': 'Catálogo de registros seccionales',
    }

    for key, desc in descriptions.items():
        if key in table_name.lower():
            return desc

    return 'Dataset del proyecto'


def infer_branch_purpose(branch_name, data):
    """Infiere el propósito de una rama basándose en su nombre y contenido."""
    name_lower = branch_name.lower()

    if 'summary' in name_lower:
        return 'Revisión y resumen del proyecto. Cálculo de indicadores macroeconómicos.'
    elif 'advantages' in name_lower:
        return 'Exploración de ventajas. Integración de datos.gob.ar DNRPA (13.6M registros).'
    elif 'continue' in name_lower:
        return 'Continuación del proyecto. Dashboard interactivo datos.gob.ar. Modelos de ML.'
    elif 'dashboard' in name_lower:
        return 'Desarrollo de dashboards y visualizaciones.'
    elif 'fix' in name_lower:
        return 'Corrección de bugs y problemas.'
    elif 'sync' in name_lower:
        return 'Sincronización de datos.'
    elif 'desarrollo' in name_lower or 'main' in name_lower:
        return 'Rama principal de desarrollo.'
    else:
        # Inferir por documentación
        if 'DNRPA' in str(data.get('docs', {})):
            return 'Rama con datos DNRPA'
        elif 'DASHBOARD' in str(data.get('docs', {})):
            return 'Rama con dashboards'
        else:
            return 'Rama de desarrollo'


def main():
    """Función principal."""
    setup_logger()

    logger.info("=" * 80)
    logger.info("🗺️  ANÁLISIS COMPLETO DEL PROYECTO")
    logger.info("=" * 80)
    logger.info("\nEste script analiza:")
    logger.info("  1. Todas las ramas del repositorio Git")
    logger.info("  2. Modelos definidos en cada rama")
    logger.info("  3. Estado actual de PostgreSQL")
    logger.info("  4. Genera Excel + Markdown con inventario completo")
    logger.info("")

    # Guardar rama actual
    current_branch = get_current_branch()
    logger.info(f"Rama actual: {current_branch}")

    # Paso 1: Obtener todas las ramas
    branches = get_all_branches()

    # Paso 2: Analizar cada rama
    logger.info("\n" + "=" * 80)
    logger.info("ANALIZANDO RAMAS")
    logger.info("=" * 80)

    branches_data = {}
    for branch in branches:
        models = get_models_in_branch(branch)
        docs = get_branch_documentation(branch)

        branches_data[branch] = {
            'models': models,
            'docs': docs
        }

    # Paso 3: Obtener estado de PostgreSQL
    logger.info("\n" + "=" * 80)
    logger.info("CONSULTANDO POSTGRESQL")
    logger.info("=" * 80)

    tables_data = get_tables_in_database()

    # Paso 4: Generar Excel
    excel_file = generar_excel_inventario(branches_data, tables_data)

    # Paso 5: Generar Markdown
    md_file = generar_markdown_proyecto(branches_data, tables_data)

    # Resumen final
    logger.info("\n" + "=" * 80)
    logger.success("✅ ANÁLISIS COMPLETADO")
    logger.info("=" * 80)
    logger.info(f"\n📊 Archivos generados:")
    logger.info(f"  1. Excel: {excel_file}")
    logger.info(f"  2. Markdown: {md_file}")
    logger.info(f"\n📈 Estadísticas:")
    logger.info(f"  Ramas analizadas: {len(branches_data)}")
    logger.info(f"  Tablas en PostgreSQL: {len(tables_data)}")
    logger.info(f"  Registros totales: {sum(t['registros'] for t in tables_data):,}")
    logger.info("\n💡 Próximos pasos:")
    logger.info(f"  - Revisa el Excel para ver inventario de datasets")
    logger.info(f"  - Lee el Markdown para documentación completa")
    logger.info(f"  - Usa estos archivos para comenzar futuras sesiones")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
