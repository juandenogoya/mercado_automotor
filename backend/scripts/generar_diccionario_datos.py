"""
Script para generar diccionario de datos de todos los datasets en PostgreSQL.

Genera un Excel con una hoja por cada dataset, mostrando:
- Nombre de cada variable/columna
- Tipo de dato
- Si permite valores NULL
- Descripción (del docstring del modelo)

Uso:
    python backend/scripts/generar_diccionario_datos.py
    python backend/scripts/generar_diccionario_datos.py --output diccionario_datos.xlsx
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from loguru import logger
from backend.config.logger import setup_logger
from backend.utils.database import get_db, engine
from backend.models import (
    Patentamiento,
    Produccion,
    BCRAIndicador,
    MercadoLibreListing,
    IPC,
    IPCDiario,
    BADLAR,
    TipoCambio,
    IndicadorCalculado
)
from sqlalchemy import inspect


def get_column_info(model):
    """
    Obtiene información de las columnas de un modelo SQLAlchemy.

    Returns:
        Lista de diccionarios con información de cada columna
    """
    inspector = inspect(model)
    columns_info = []

    for column in inspector.columns:
        col_info = {
            'Columna': column.name,
            'Tipo de Dato': str(column.type),
            'Permite NULL': 'Sí' if column.nullable else 'No',
            'Clave Primaria': 'Sí' if column.primary_key else 'No',
            'Única': 'Sí' if column.unique else 'No',
            'Default': str(column.default.arg) if column.default else '-',
        }
        columns_info.append(col_info)

    return columns_info


def get_table_description(model):
    """Obtiene descripción del modelo desde el docstring."""
    if model.__doc__:
        # Tomar primera línea del docstring
        lines = [line.strip() for line in model.__doc__.split('\n') if line.strip()]
        if lines:
            return lines[0]
    return "Sin descripción"


def get_record_count(model):
    """Obtiene el número de registros en la tabla."""
    try:
        with get_db() as db:
            count = db.query(model).count()
        return count
    except:
        return 0


def generar_diccionario_datos(output_file='diccionario_datos.xlsx'):
    """
    Genera un Excel con el diccionario de datos de todos los datasets.
    """
    logger.info("="*80)
    logger.info("📚 GENERANDO DICCIONARIO DE DATOS")
    logger.info("="*80)

    # Definir modelos a documentar
    datasets = {
        'Patentamientos': Patentamiento,
        'Producción': Produccion,
        'BCRA Indicadores': BCRAIndicador,
        'MercadoLibre Listings': MercadoLibreListing,
        'IPC Mensual': IPC,
        'IPC Diario': IPCDiario,
        'BADLAR': BADLAR,
        'Tipo de Cambio': TipoCambio,
        'Indicadores Calculados': IndicadorCalculado,
    }

    logger.info(f"\nDatasets a documentar: {len(datasets)}")

    # Crear Excel
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

            # Crear hoja de índice
            logger.info("\n📋 Creando hoja de índice...")
            indice_data = []

            for nombre, model in datasets.items():
                descripcion = get_table_description(model)
                count = get_record_count(model)
                num_columnas = len(inspect(model).columns)

                indice_data.append({
                    'Dataset': nombre,
                    'Tabla': model.__tablename__,
                    'Descripción': descripcion,
                    'Registros': f"{count:,}",
                    'Variables': num_columnas
                })

                logger.info(f"  ✓ {nombre:30s} - {num_columnas} variables, {count:,} registros")

            df_indice = pd.DataFrame(indice_data)
            df_indice.to_excel(writer, sheet_name='📋 Índice', index=False)

            # Crear una hoja por cada dataset
            logger.info("\n📊 Generando hojas por dataset...")

            for nombre, model in datasets.items():
                logger.info(f"\n  Procesando: {nombre}...")

                # Obtener información de columnas
                columns_info = get_column_info(model)
                df_columns = pd.DataFrame(columns_info)

                # Información general del dataset
                descripcion = get_table_description(model)
                count = get_record_count(model)

                # Crear DataFrame con metadata
                metadata = pd.DataFrame([
                    {'Propiedad': 'Nombre del Dataset', 'Valor': nombre},
                    {'Propiedad': 'Tabla en PostgreSQL', 'Valor': model.__tablename__},
                    {'Propiedad': 'Descripción', 'Valor': descripcion},
                    {'Propiedad': 'Total de Registros', 'Valor': f"{count:,}"},
                    {'Propiedad': 'Total de Variables', 'Valor': len(columns_info)},
                    {'Propiedad': 'Fecha de Generación', 'Valor': datetime.now().strftime('%Y-%m-%d %H:%M')},
                ])

                # Limpiar nombre de hoja (max 31 caracteres)
                sheet_name = nombre[:28] + "..." if len(nombre) > 31 else nombre

                # Escribir metadata primero
                metadata.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)

                # Escribir columnas después (con un espacio)
                df_columns.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False,
                    startrow=len(metadata) + 2
                )

                # Formatear hoja
                worksheet = writer.sheets[sheet_name]

                # Ajustar anchos de columnas
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

                logger.info(f"    ✓ {len(columns_info)} variables documentadas")

        logger.success(f"\n✅ Diccionario de datos generado: {output_file}")
        logger.info(f"   Hojas creadas: {len(datasets) + 1} (Índice + {len(datasets)} datasets)")

        return output_file

    except Exception as e:
        logger.error(f"❌ Error generando Excel: {e}")
        raise


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Generar diccionario de datos de todos los datasets en PostgreSQL"
    )

    parser.add_argument(
        '--output',
        type=str,
        default='diccionario_datos.xlsx',
        help='Nombre del archivo Excel de salida (default: diccionario_datos.xlsx)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logger()

    logger.info("="*80)
    logger.info("📚 GENERADOR DE DICCIONARIO DE DATOS")
    logger.info("="*80)
    logger.info("\nEste script genera un Excel con:")
    logger.info("  - Hoja de índice con resumen de todos los datasets")
    logger.info("  - Una hoja por dataset con listado de variables")
    logger.info("  - Información de tipo de dato, nullabilidad, claves")
    logger.info("")

    output_file = generar_diccionario_datos(args.output)

    logger.info("\n" + "="*80)
    logger.success("✅ PROCESO COMPLETADO")
    logger.info("="*80)
    logger.info(f"  Archivo generado: {output_file}")
    logger.info("\n📖 El Excel contiene:")
    logger.info("  - Hoja 'Índice': Resumen de todos los datasets")
    logger.info("  - 9 hojas adicionales: Una por cada dataset")
    logger.info("\n💡 Usa este diccionario para:")
    logger.info("  - Conocer qué variables tiene cada dataset")
    logger.info("  - Planificar joins entre datasets")
    logger.info("  - Diseñar modelos de ML")
    logger.info("  - Documentación del proyecto")
    logger.info("="*80)


if __name__ == "__main__":
    main()
