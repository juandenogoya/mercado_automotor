"""
Script para generar diccionario completo de datos de todos los datasets en PostgreSQL.

Genera Excel con:
- Nombre del dataset
- Variables (columnas) con tipos de datos
- Columnas calculadas con fórmulas
- Fuente de construcción (API, scraper, etc.)

Uso:
    python backend/scripts/generar_diccionario_completo.py
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from sqlalchemy import inspect, text
from collections import OrderedDict

root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

try:
    from backend.utils.database import get_db, engine
    from backend.config.logger import setup_logger
    from loguru import logger
except:
    # Fallback sin loguru
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    from backend.utils.database import get_db, engine


# Mapeo de fuentes de datos
FUENTES_DATOS = {
    'ipc': {
        'fuente': 'INDEC API - Series de Tiempo',
        'url': 'https://apis.datos.gob.ar/series/api/',
        'tipo': 'API REST',
        'frecuencia': 'Mensual',
        'script': 'backend/scripts/cargar_ipc_indec.py'
    },
    'ipc_diario': {
        'fuente': 'Calculado desde IPC Mensual',
        'url': 'N/A (expansión local)',
        'tipo': 'Transformación',
        'frecuencia': 'Diaria',
        'script': 'manage.py expandir-ipc-diario'
    },
    'badlar': {
        'fuente': 'BCRA API v4.0',
        'url': 'https://api.bcra.gob.ar/estadisticas/v4.0',
        'tipo': 'API REST',
        'frecuencia': 'Diaria',
        'script': 'backend/api_clients/bcra_client.py'
    },
    'tipo_cambio': {
        'fuente': 'BCRA API v4.0',
        'url': 'https://api.bcra.gob.ar/estadisticas/v4.0',
        'tipo': 'API REST',
        'frecuencia': 'Diaria',
        'script': 'backend/api_clients/bcra_client.py'
    },
    'tc_': {
        'fuente': 'BCRA API v4.0',
        'url': 'https://api.bcra.gob.ar/estadisticas/v4.0',
        'tipo': 'API REST',
        'frecuencia': 'Diaria',
        'script': 'backend/api_clients/bcra_client.py'
    },
    'indicadores_calculados': {
        'fuente': 'Cálculos desde IPC, BADLAR, Tipo de Cambio',
        'url': 'N/A (cálculo local)',
        'tipo': 'Transformación',
        'frecuencia': 'Diaria',
        'script': 'backend/scripts/calcular_indicadores_macro.py'
    },
    'patentamientos': {
        'fuente': 'ACARA - Web Scraping',
        'url': 'https://www.acara.org.ar/',
        'tipo': 'Web Scraping',
        'frecuencia': 'Mensual',
        'script': 'backend/scrapers/acara_scraper.py'
    },
    'produccion': {
        'fuente': 'ADEFA - Web Scraping',
        'url': 'https://www.adefa.org.ar/',
        'tipo': 'Web Scraping',
        'frecuencia': 'Mensual',
        'script': 'backend/scrapers/adefa_scraper.py'
    },
    'bcra_indicadores': {
        'fuente': 'BCRA API v2.0',
        'url': 'https://api.bcra.gob.ar/estadisticas/v2.0',
        'tipo': 'API REST',
        'frecuencia': 'Diaria',
        'script': 'backend/api_clients/bcra_client.py'
    },
    'mercadolibre': {
        'fuente': 'MercadoLibre API',
        'url': 'https://api.mercadolibre.com/',
        'tipo': 'API REST',
        'frecuencia': 'Bajo demanda',
        'script': 'backend/api_clients/mercadolibre_client.py'
    },
    'datos_gob_inscripciones': {
        'fuente': 'datos.gob.ar - DNRPA',
        'url': 'https://datos.gob.ar/dataset/justicia-estadistica-inscripciones-iniciales',
        'tipo': 'Archivo CSV (descarga manual)',
        'frecuencia': 'Actualización trimestral',
        'script': 'backend/scripts/cargar_datos_gob_ar_postgresql.py'
    },
    'datos_gob_transferencias': {
        'fuente': 'datos.gob.ar - DNRPA',
        'url': 'https://datos.gob.ar/dataset/justicia-estadistica-transferencias',
        'tipo': 'Archivo CSV (descarga manual)',
        'frecuencia': 'Actualización trimestral',
        'script': 'backend/scripts/cargar_datos_gob_ar_postgresql.py'
    },
    'datos_gob_prendas': {
        'fuente': 'datos.gob.ar - DNRPA',
        'url': 'https://datos.gob.ar/dataset/justicia-estadistica-prendas',
        'tipo': 'Archivo CSV (descarga manual)',
        'frecuencia': 'Actualización trimestral',
        'script': 'backend/scripts/cargar_datos_gob_ar_postgresql.py'
    },
    'datos_gob_registros_seccionales': {
        'fuente': 'datos.gob.ar - DNRPA',
        'url': 'https://datos.gob.ar/dataset/justicia-registros-seccionales',
        'tipo': 'Archivo CSV (descarga manual)',
        'frecuencia': 'Estático (catálogo)',
        'script': 'backend/scripts/cargar_datos_gob_ar_postgresql.py'
    }
}

# Columnas calculadas conocidas
COLUMNAS_CALCULADAS = {
    'ipc_diario': {
        'ipc_mensual': 'Promedio ponderado del IPC mensual del mes correspondiente',
        'variacion_mensual': 'Calculado desde nivel_general del mes anterior',
        'variacion_interanual': 'Calculado desde nivel_general de hace 12 meses'
    },
    'indicadores_calculados': {
        'tasa_real': 'BADLAR - IPC_anualizado (Fisher equation)',
        'tcr': 'tipo_cambio_nominal / (ipc_acumulado / 100)',
        'accesibilidad': '(TCR × Tasa_Real) / IPC_Acumulado × 100',
        'volatilidad': 'Promedio de desviaciones estándar móviles (30 días) de IPC, BADLAR y TC'
    },
    'datos_gob_inscripciones': {
        'edad_titular': 'YEAR(tramite_fecha) - titular_anio_nacimiento',
        'edad_vehiculo': 'YEAR(tramite_fecha) - automotor_anio_modelo'
    },
    'datos_gob_transferencias': {
        'edad_titular': 'YEAR(tramite_fecha) - titular_anio_nacimiento',
        'edad_vehiculo': 'YEAR(tramite_fecha) - automotor_anio_modelo'
    },
    'datos_gob_prendas': {
        'edad_titular': 'YEAR(tramite_fecha) - titular_anio_nacimiento',
        'edad_vehiculo': 'YEAR(tramite_fecha) - automotor_anio_modelo'
    }
}


def get_fuente_info(tabla_nombre):
    """Obtiene información de la fuente de datos para una tabla."""
    for key, info in FUENTES_DATOS.items():
        if key in tabla_nombre.lower():
            return info

    return {
        'fuente': 'No documentado',
        'url': 'N/A',
        'tipo': 'Desconocido',
        'frecuencia': 'N/A',
        'script': 'N/A'
    }


def mapear_tipo_sql_a_python(tipo_sql):
    """Mapea tipos de SQL a tipos de Python."""
    tipo_sql_lower = str(tipo_sql).lower()

    if 'int' in tipo_sql_lower or 'serial' in tipo_sql_lower:
        return 'int'
    elif 'float' in tipo_sql_lower or 'double' in tipo_sql_lower or 'real' in tipo_sql_lower:
        return 'float'
    elif 'numeric' in tipo_sql_lower or 'decimal' in tipo_sql_lower:
        return 'float (decimal)'
    elif 'varchar' in tipo_sql_lower or 'text' in tipo_sql_lower or 'char' in tipo_sql_lower:
        return 'str (object)'
    elif 'date' in tipo_sql_lower or 'time' in tipo_sql_lower:
        return 'datetime'
    elif 'bool' in tipo_sql_lower:
        return 'bool'
    elif 'json' in tipo_sql_lower:
        return 'dict (json)'
    else:
        return f'object ({tipo_sql})'


def get_columna_calculada_info(tabla_nombre, columna_nombre):
    """Obtiene información si la columna es calculada."""
    if tabla_nombre in COLUMNAS_CALCULADAS:
        if columna_nombre in COLUMNAS_CALCULADAS[tabla_nombre]:
            return COLUMNAS_CALCULADAS[tabla_nombre][columna_nombre]
    return None


def analizar_postgresql():
    """Analiza todas las tablas en PostgreSQL."""
    logger.info("=" * 80)
    logger.info("📊 ANALIZANDO POSTGRESQL")
    logger.info("=" * 80)

    inspector = inspect(engine)
    tablas = inspector.get_table_names()

    logger.info(f"✓ Encontradas {len(tablas)} tablas")

    tablas_info = []

    for tabla in sorted(tablas):
        logger.info(f"\n  Analizando tabla: {tabla}")

        try:
            # Obtener columnas
            columnas = inspector.get_columns(tabla)

            # Obtener conteo de registros
            with get_db() as db:
                result = db.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
                count = result.scalar()

            # Obtener fuente de datos
            fuente_info = get_fuente_info(tabla)

            # Información de cada columna
            columnas_detalle = []
            for col in columnas:
                tipo_python = mapear_tipo_sql_a_python(col['type'])
                es_calculada = get_columna_calculada_info(tabla, col['name'])

                columnas_detalle.append({
                    'columna': col['name'],
                    'tipo_sql': str(col['type']),
                    'tipo_python': tipo_python,
                    'nullable': 'Sí' if col['nullable'] else 'No',
                    'es_calculada': 'Sí' if es_calculada else 'No',
                    'formula_calculo': es_calculada if es_calculada else 'N/A'
                })

            tablas_info.append({
                'tabla': tabla,
                'registros': count,
                'columnas_count': len(columnas),
                'columnas': columnas_detalle,
                'fuente': fuente_info['fuente'],
                'url': fuente_info['url'],
                'tipo': fuente_info['tipo'],
                'frecuencia': fuente_info['frecuencia'],
                'script': fuente_info['script']
            })

            logger.info(f"    ✓ {len(columnas)} columnas, {count:,} registros")

        except Exception as e:
            logger.error(f"    ❌ Error analizando {tabla}: {e}")

    return tablas_info


def generar_excel_diccionario(tablas_info, output_file='DICCIONARIO_COMPLETO_DATASETS.xlsx'):
    """Genera Excel con diccionario completo de datos."""
    logger.info("\n" + "=" * 80)
    logger.info("📝 GENERANDO EXCEL DICCIONARIO")
    logger.info("=" * 80)

    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

            # Hoja 1: Índice de Tablas
            logger.info("\n📋 Hoja 1: Índice de Tablas")
            indice_data = []
            for info in tablas_info:
                indice_data.append({
                    'Tabla': info['tabla'],
                    'Registros': f"{info['registros']:,}",
                    'Columnas': info['columnas_count'],
                    'Fuente': info['fuente'],
                    'Tipo': info['tipo'],
                    'Frecuencia': info['frecuencia']
                })

            df_indice = pd.DataFrame(indice_data)
            df_indice.to_excel(writer, sheet_name='📋 Índice', index=False)

            # Hoja 2: Resumen de Fuentes
            logger.info("\n🌐 Hoja 2: Fuentes de Datos")
            fuentes_data = []
            for info in tablas_info:
                fuentes_data.append({
                    'Tabla': info['tabla'],
                    'Fuente': info['fuente'],
                    'URL': info['url'],
                    'Tipo de Acceso': info['tipo'],
                    'Frecuencia': info['frecuencia'],
                    'Script': info['script']
                })

            df_fuentes = pd.DataFrame(fuentes_data)
            df_fuentes.to_excel(writer, sheet_name='🌐 Fuentes', index=False)

            # Hoja 3+: Una hoja por cada tabla
            logger.info("\n📊 Generando hojas individuales por tabla...")
            for info in tablas_info:
                tabla_nombre = info['tabla']

                # Nombre de hoja (max 31 caracteres)
                sheet_name = tabla_nombre[:28] + '...' if len(tabla_nombre) > 31 else tabla_nombre

                logger.info(f"  - {tabla_nombre}")

                # DataFrame con columnas
                df_tabla = pd.DataFrame(info['columnas'])

                # Reordenar columnas
                df_tabla = df_tabla[[
                    'columna',
                    'tipo_python',
                    'tipo_sql',
                    'nullable',
                    'es_calculada',
                    'formula_calculo'
                ]]

                df_tabla.columns = [
                    'Columna',
                    'Tipo Python',
                    'Tipo SQL',
                    'Permite NULL',
                    'Es Calculada',
                    'Fórmula de Cálculo'
                ]

                df_tabla.to_excel(writer, sheet_name=sheet_name, index=False)

            # Hoja Final: Resumen Ejecutivo
            logger.info("\n📈 Hoja Final: Resumen Ejecutivo")
            resumen_data = [
                {'Métrica': 'Total de Tablas', 'Valor': len(tablas_info)},
                {'Métrica': 'Total de Columnas', 'Valor': sum(t['columnas_count'] for t in tablas_info)},
                {'Métrica': 'Total de Registros', 'Valor': f"{sum(t['registros'] for t in tablas_info):,}"},
                {'Métrica': 'Fecha de Generación', 'Valor': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                {'Métrica': 'Proyecto', 'Valor': 'Mercado Automotor - Inteligencia Comercial'},
                {'Métrica': 'Base de Datos', 'Valor': 'PostgreSQL 15 + TimescaleDB'},
            ]

            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='📈 Resumen', index=False)

            # Ajustar anchos de columnas
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if cell.value and len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 100)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        logger.success(f"\n✅ Excel generado: {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"❌ Error generando Excel: {e}")
        raise


def main():
    """Función principal."""
    try:
        setup_logger()
    except:
        pass

    logger.info("=" * 80)
    logger.info("📚 GENERADOR DE DICCIONARIO COMPLETO DE DATASETS")
    logger.info("=" * 80)
    logger.info("\nEste script genera:")
    logger.info("  1. Índice de todas las tablas en PostgreSQL")
    logger.info("  2. Detalle de columnas con tipos de datos")
    logger.info("  3. Identificación de columnas calculadas con fórmulas")
    logger.info("  4. Fuentes de datos (API, scraper, archivo)")
    logger.info("")

    # Paso 1: Analizar PostgreSQL
    tablas_info = analizar_postgresql()

    # Paso 2: Generar Excel
    excel_file = generar_excel_diccionario(tablas_info)

    # Resumen final
    logger.info("\n" + "=" * 80)
    logger.info("✅ PROCESO COMPLETADO")
    logger.info("=" * 80)
    logger.info(f"\n📊 Archivo generado: {excel_file}")
    logger.info(f"\n📈 Estadísticas:")
    logger.info(f"  Tablas analizadas: {len(tablas_info)}")
    logger.info(f"  Columnas totales: {sum(t['columnas_count'] for t in tablas_info)}")
    logger.info(f"  Registros totales: {sum(t['registros'] for t in tablas_info):,}")
    logger.info("\n💡 Abre el Excel para ver el diccionario completo de datos")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
