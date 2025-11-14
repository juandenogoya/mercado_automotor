"""
Script standalone para generar diccionario completo de datos de PostgreSQL.

Genera Excel con:
- Nombre del dataset
- Variables (columnas) con tipos de datos
- Columnas calculadas con fórmulas
- Fuente de construcción (API, scraper, etc.)

Uso:
    python backend/scripts/generar_diccionario_standalone.py
"""
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from urllib.parse import quote_plus
from sqlalchemy import create_engine, inspect, text
from contextlib import contextmanager


# Configuración de base de datos desde variables de entorno
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'mercado_automotor')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Construir URL escapando caracteres especiales en password
DATABASE_URL = f"postgresql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def log(message):
    """Simple logging."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


@contextmanager
def get_db():
    """Context manager para sesión de BD."""
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()


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
        'fuente': 'datos.gob.ar - DNRPA (Inscripciones Iniciales 0km)',
        'url': 'https://datos.gob.ar/dataset/justicia-estadistica-inscripciones-iniciales',
        'tipo': 'Archivo CSV (descarga manual)',
        'frecuencia': 'Actualización trimestral',
        'script': 'backend/scripts/cargar_datos_gob_ar_postgresql.py',
        'registros_esperados': '~3M (2.97M en datos.gob.ar)'
    },
    'datos_gob_transferencias': {
        'fuente': 'datos.gob.ar - DNRPA (Transferencias Vehículos Usados)',
        'url': 'https://datos.gob.ar/dataset/justicia-estadistica-transferencias',
        'tipo': 'Archivo CSV (descarga manual)',
        'frecuencia': 'Actualización trimestral',
        'script': 'backend/scripts/cargar_datos_gob_ar_postgresql.py',
        'registros_esperados': '~9M (8.83M en datos.gob.ar)'
    },
    'datos_gob_prendas': {
        'fuente': 'datos.gob.ar - DNRPA (Prendas Vehículos Financiados)',
        'url': 'https://datos.gob.ar/dataset/justicia-estadistica-prendas',
        'tipo': 'Archivo CSV (descarga manual)',
        'frecuencia': 'Actualización trimestral',
        'script': 'backend/scripts/cargar_datos_gob_ar_postgresql.py',
        'registros_esperados': '~2M (1.79M en datos.gob.ar)'
    },
    'datos_gob_registros_seccionales': {
        'fuente': 'datos.gob.ar - DNRPA (Catálogo Registros)',
        'url': 'https://datos.gob.ar/dataset/justicia-registros-seccionales',
        'tipo': 'Archivo CSV (descarga manual)',
        'frecuencia': 'Estático (catálogo)',
        'script': 'backend/scripts/cargar_datos_gob_ar_postgresql.py',
        'registros_esperados': '~1,500 registros'
    }
}

# Columnas calculadas conocidas
COLUMNAS_CALCULADAS = {
    'ipc_diario': {
        'ipc_mensual': 'Promedio ponderado del IPC mensual vigente (Opción B: vigencia)',
        'variacion_mensual': 'Calculado: ((nivel_actual - nivel_anterior) / nivel_anterior) × 100',
        'variacion_interanual': 'Calculado: ((nivel_actual - nivel_hace_12_meses) / nivel_hace_12_meses) × 100'
    },
    'indicadores_calculados': {
        'tasa_real': 'BADLAR - IPC_anualizado | Fisher: ((1 + BADLAR/100) / (1 + IPC_mensual/100))^12 - 1',
        'tcr': 'tipo_cambio_nominal / (ipc_acumulado / 100) | Tipo de Cambio Real',
        'accesibilidad': '(TCR × (100 + Tasa_Real)) / IPC_Acumulado × 100 | Índice normalizado base 100',
        'volatilidad': 'AVG(std_dev_30d(IPC), std_dev_30d(BADLAR), std_dev_30d(TC)) | Promedio de volatilidades'
    },
    'datos_gob_inscripciones': {
        'edad_titular': 'EXTRACT(YEAR FROM tramite_fecha) - titular_anio_nacimiento | Edad del cliente al momento del trámite',
        'edad_vehiculo': 'EXTRACT(YEAR FROM tramite_fecha) - automotor_anio_modelo | Antigüedad del vehículo'
    },
    'datos_gob_transferencias': {
        'edad_titular': 'EXTRACT(YEAR FROM tramite_fecha) - titular_anio_nacimiento | Edad del cliente al momento del trámite',
        'edad_vehiculo': 'EXTRACT(YEAR FROM tramite_fecha) - automotor_anio_modelo | Antigüedad del vehículo'
    },
    'datos_gob_prendas': {
        'edad_titular': 'EXTRACT(YEAR FROM tramite_fecha) - titular_anio_nacimiento | Edad del cliente al momento del trámite',
        'edad_vehiculo': 'EXTRACT(YEAR FROM tramite_fecha) - automotor_anio_modelo | Antigüedad del vehículo'
    },
    'ipc': {
        'variacion_mensual': 'Calculado: ((nivel_general_actual - nivel_general_anterior) / nivel_general_anterior) × 100',
        'variacion_interanual': 'Calculado: ((nivel_general_actual - nivel_general_hace_12m) / nivel_general_hace_12m) × 100',
        'variacion_acumulada': 'Calculado: ((nivel_general_actual - nivel_general_enero) / nivel_general_enero) × 100'
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
        return 'Decimal (float)'
    elif 'varchar' in tipo_sql_lower or 'text' in tipo_sql_lower or 'char' in tipo_sql_lower:
        return 'str'
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
    log("=" * 80)
    log("📊 ANALIZANDO POSTGRESQL")
    log("=" * 80)

    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    tablas = inspector.get_table_names()

    log(f"✓ Encontradas {len(tablas)} tablas")

    tablas_info = []

    with get_db() as db:
        for tabla in sorted(tablas):
            log(f"\n  Analizando tabla: {tabla}")

            try:
                # Obtener columnas
                columnas = inspector.get_columns(tabla)

                # Obtener conteo de registros
                result = db.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
                count = result.fetchone()[0]

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
                    'script': fuente_info['script'],
                    'registros_esperados': fuente_info.get('registros_esperados', 'N/A')
                })

                log(f"    ✓ {len(columnas)} columnas, {count:,} registros")

            except Exception as e:
                log(f"    ❌ Error analizando {tabla}: {e}")

    return tablas_info


def generar_excel_diccionario(tablas_info, output_file='DICCIONARIO_COMPLETO_DATASETS.xlsx'):
    """Genera Excel con diccionario completo de datos."""
    log("\n" + "=" * 80)
    log("📝 GENERANDO EXCEL DICCIONARIO")
    log("=" * 80)

    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

            # Hoja 1: Índice de Tablas
            log("\n📋 Hoja 1: Índice de Tablas")
            indice_data = []
            for info in tablas_info:
                indice_data.append({
                    'Tabla': info['tabla'],
                    'Registros Actuales': f"{info['registros']:,}",
                    'Registros Esperados': info['registros_esperados'],
                    'Columnas': info['columnas_count'],
                    'Fuente': info['fuente'],
                    'Tipo': info['tipo']
                })

            df_indice = pd.DataFrame(indice_data)
            df_indice.to_excel(writer, sheet_name='📋 Índice', index=False)

            # Hoja 2: Resumen de Fuentes
            log("\n🌐 Hoja 2: Fuentes de Datos")
            fuentes_data = []
            for info in tablas_info:
                fuentes_data.append({
                    'Tabla': info['tabla'],
                    'Fuente': info['fuente'],
                    'URL': info['url'],
                    'Tipo de Acceso': info['tipo'],
                    'Frecuencia Actualización': info['frecuencia'],
                    'Script de Carga': info['script']
                })

            df_fuentes = pd.DataFrame(fuentes_data)
            df_fuentes.to_excel(writer, sheet_name='🌐 Fuentes', index=False)

            # Hoja 3+: Una hoja por cada tabla
            log("\n📊 Generando hojas individuales por tabla...")
            for info in tablas_info:
                tabla_nombre = info['tabla']

                # Nombre de hoja (max 31 caracteres para Excel)
                sheet_name = tabla_nombre[:28] + '...' if len(tabla_nombre) > 31 else tabla_nombre

                log(f"  - {tabla_nombre}")

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
                    'Fórmula / Descripción'
                ]

                df_tabla.to_excel(writer, sheet_name=sheet_name, index=False)

            # Hoja Final: Resumen Ejecutivo
            log("\n📈 Hoja Final: Resumen Ejecutivo")
            resumen_data = [
                {'Métrica': 'Total de Tablas', 'Valor': len(tablas_info)},
                {'Métrica': 'Total de Columnas', 'Valor': sum(t['columnas_count'] for t in tablas_info)},
                {'Métrica': 'Total de Registros', 'Valor': f"{sum(t['registros'] for t in tablas_info):,}"},
                {'Métrica': 'Fecha de Generación', 'Valor': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                {'Métrica': 'Proyecto', 'Valor': 'Mercado Automotor - Inteligencia Comercial'},
                {'Métrica': 'Base de Datos', 'Valor': f'PostgreSQL ({DB_HOST}:{DB_PORT}/{DB_NAME})'},
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

        log(f"\n✅ Excel generado: {output_file}")
        return output_file

    except Exception as e:
        log(f"❌ Error generando Excel: {e}")
        raise


def main():
    """Función principal."""
    log("=" * 80)
    log("📚 GENERADOR DE DICCIONARIO COMPLETO DE DATASETS")
    log("=" * 80)
    log("\nEste script genera:")
    log("  1. Índice de todas las tablas en PostgreSQL")
    log("  2. Detalle de columnas con tipos de datos (Python y SQL)")
    log("  3. Identificación de columnas calculadas con fórmulas")
    log("  4. Fuentes de datos (API, scraper, archivo CSV)")
    log("  5. Scripts de carga correspondientes")
    log("")

    # Paso 1: Analizar PostgreSQL
    tablas_info = analizar_postgresql()

    if not tablas_info:
        log("\n⚠️  No se encontraron tablas en la base de datos")
        return

    # Paso 2: Generar Excel
    excel_file = generar_excel_diccionario(tablas_info)

    # Resumen final
    log("\n" + "=" * 80)
    log("✅ PROCESO COMPLETADO")
    log("=" * 80)
    log(f"\n📊 Archivo generado: {excel_file}")
    log(f"\n📈 Estadísticas:")
    log(f"  Tablas analizadas: {len(tablas_info)}")
    log(f"  Columnas totales: {sum(t['columnas_count'] for t in tablas_info)}")
    log(f"  Registros totales: {sum(t['registros'] for t in tablas_info):,}")
    log("\n💡 El Excel contiene:")
    log("  - Hoja 'Índice': Resumen de todas las tablas")
    log("  - Hoja 'Fuentes': URLs y tipos de acceso a datos")
    log("  - Hojas individuales: Detalle de columnas por tabla")
    log("  - Hoja 'Resumen': Estadísticas generales")
    log("\n📁 Abre el Excel para ver el diccionario completo de datos")
    log("=" * 80)


if __name__ == "__main__":
    main()
