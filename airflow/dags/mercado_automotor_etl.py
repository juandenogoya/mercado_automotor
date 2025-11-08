"""
DAG principal de ETL - Mercado Automotor
Orchestración de scraping, APIs y procesamiento de datos
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, '/opt/airflow/backend')

from backend.scrapers import AcaraScraper, AdefaScraper, DNRPAScraper
from backend.api_clients import BCRAClient, MercadoLibreClient, INDECClient
from backend.analytics.indicadores import (
    calcular_tension_demanda,
    calcular_rotacion_stock,
    calcular_accesibilidad_compra,
    calcular_ranking_atencion,
    guardar_indicadores
)
from backend.utils.database import get_db
from loguru import logger


# Default args
default_args = {
    'owner': 'mercado_automotor',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}


# ==================== TASK FUNCTIONS ====================

def scrape_acara():
    """Task: Scrape ACARA patentamientos."""
    logger.info("Starting ACARA scraping...")

    try:
        with AcaraScraper() as scraper:
            result = scraper.scrape()
            logger.info(f"ACARA scraping result: {result}")
            return result
    except Exception as e:
        logger.error(f"ACARA scraping failed: {e}")
        raise


def scrape_adefa():
    """Task: Scrape ADEFA producción."""
    logger.info("Starting ADEFA scraping...")

    try:
        with AdefaScraper() as scraper:
            result = scraper.scrape()
            logger.info(f"ADEFA scraping result: {result}")
            return result
    except Exception as e:
        logger.error(f"ADEFA scraping failed: {e}")
        raise


def scrape_dnrpa():
    """Task: Scrape DNRPA patentamientos oficiales con detalle provincial."""
    logger.info("Starting DNRPA scraping...")

    try:
        scraper = DNRPAScraper()

        # Scrape año actual, autos (puede expandirse a motos y maquinarias)
        anio_actual = datetime.now().year

        # Autos
        logger.info("Scraping DNRPA - Autos...")
        result_autos = scraper.scrape_all_provincias(
            anio=anio_actual,
            codigo_tipo='A',
            incluir_detalle=True
        )

        # Guardar en BD
        total_guardados = 0

        if result_autos['resumen_provincial'] is not None:
            guardados = scraper.save_to_database(
                result_autos['resumen_provincial'],
                tipo_vehiculo='0km'
            )
            total_guardados += guardados

        for codigo_prov, df_detalle in result_autos['detalles'].items():
            guardados = scraper.save_to_database(df_detalle, tipo_vehiculo='0km')
            total_guardados += guardados

        logger.info(f"DNRPA Autos: {total_guardados} registros guardados")

        # Opcional: Motos (comentado, activar si se necesita)
        # logger.info("Scraping DNRPA - Motos...")
        # result_motos = scraper.scrape_all_provincias(
        #     anio=anio_actual,
        #     codigo_tipo='M',
        #     incluir_detalle=False  # Solo resumen para motos
        # )

        final_result = {
            'status': 'success',
            'anio': anio_actual,
            'autos_guardados': total_guardados,
            'provincias': len(result_autos['detalles']),
            'errores': result_autos['errores']
        }

        logger.info(f"DNRPA scraping result: {final_result}")
        return final_result

    except Exception as e:
        logger.error(f"DNRPA scraping failed: {e}")
        raise


def sync_bcra():
    """Task: Sync BCRA indicators."""
    logger.info("Starting BCRA sync...")

    try:
        client = BCRAClient()
        result = client.sync_all_indicators()
        logger.info(f"BCRA sync result: {result}")
        return result
    except Exception as e:
        logger.error(f"BCRA sync failed: {e}")
        raise


def scrape_mercadolibre():
    """Task: Scrape MercadoLibre market snapshot."""
    logger.info("Starting MercadoLibre scraping...")

    try:
        client = MercadoLibreClient()
        result = client.scrape_market_snapshot(
            marcas=["Toyota", "Ford", "Volkswagen", "Chevrolet", "Fiat"],
            max_items_por_marca=50
        )
        logger.info(f"MercadoLibre scraping result: {result}")
        return result
    except Exception as e:
        logger.error(f"MercadoLibre scraping failed: {e}")
        raise


def sync_indec():
    """Task: Sync INDEC indicators (IPC, salario)."""
    logger.info("Starting INDEC sync...")

    try:
        client = INDECClient()
        result = client.sync_all_indicators(meses_atras=12)
        logger.info(f"INDEC sync result: {result}")
        return result
    except Exception as e:
        logger.error(f"INDEC sync failed: {e}")
        raise


def calculate_indicators():
    """Task: Calculate derived indicators."""
    logger.info("Calculating indicators...")

    try:
        with get_db() as db:
            fecha_hasta = datetime.now().date()
            fecha_desde = fecha_hasta - timedelta(days=90)  # Últimos 90 días

            total_indicadores = 0

            # 1. Índice de tensión de demanda
            logger.info("Calculando Índice de Tensión de Demanda...")
            indicadores_tension = calcular_tension_demanda(
                db=db,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
            saved = guardar_indicadores(db, indicadores_tension)
            total_indicadores += saved
            logger.info(f"✓ Tensión de demanda: {saved} indicadores guardados")

            # 2. Rotación de stock
            logger.info("Calculando Rotación de Stock...")
            indicadores_rotacion = calcular_rotacion_stock(
                db=db,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
            saved = guardar_indicadores(db, indicadores_rotacion)
            total_indicadores += saved
            logger.info(f"✓ Rotación de stock: {saved} indicadores guardados")

            # 3. Accesibilidad de compra (obtiene salario de INDEC automáticamente)
            logger.info("Calculando Índice de Accesibilidad de Compra...")
            indicadores_accesibilidad = calcular_accesibilidad_compra(
                db=db,
                fecha=fecha_hasta
                # salario_promedio se obtiene automáticamente del INDEC
            )
            saved = guardar_indicadores(db, indicadores_accesibilidad)
            total_indicadores += saved
            logger.info(f"✓ Accesibilidad de compra: {saved} indicadores guardados")

            # 4. Ranking de atención
            logger.info("Calculando Ranking de Atención...")
            indicadores_ranking = calcular_ranking_atencion(
                db=db,
                fecha=fecha_hasta,
                top_n=20
            )
            saved = guardar_indicadores(db, indicadores_ranking)
            total_indicadores += saved
            logger.info(f"✓ Ranking de atención: {saved} indicadores guardados")

            logger.success(f"✓✓ Cálculo de indicadores completado: {total_indicadores} indicadores totales")

            return {
                "status": "success",
                "total_indicadores": total_indicadores,
                "tension_demanda": len(indicadores_tension),
                "rotacion_stock": len(indicadores_rotacion),
                "accesibilidad_compra": len(indicadores_accesibilidad),
                "ranking_atencion": len(indicadores_ranking)
            }

    except Exception as e:
        logger.error(f"Error calculando indicadores: {e}")
        raise


# ==================== DAG DEFINITIONS ====================

# DAG 1: Daily ETL
with DAG(
    'mercado_automotor_daily_etl',
    default_args=default_args,
    description='ETL diario: BCRA + MercadoLibre + INDEC',
    schedule_interval='0 0 * * *',  # Daily at midnight
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mercado_automotor', 'daily', 'etl'],
) as dag_daily:

    # BCRA sync (diario)
    task_bcra = PythonOperator(
        task_id='sync_bcra_indicators',
        python_callable=sync_bcra,
    )

    # MercadoLibre snapshot (diario)
    task_meli = PythonOperator(
        task_id='scrape_mercadolibre',
        python_callable=scrape_mercadolibre,
    )

    # INDEC sync (diario - IPC, salario)
    task_indec = PythonOperator(
        task_id='sync_indec_indicators',
        python_callable=sync_indec,
    )

    # Calculate indicators
    task_indicators = PythonOperator(
        task_id='calculate_indicators',
        python_callable=calculate_indicators,
    )

    # Dependencies: BCRA, ML e INDEC en paralelo, luego calcular indicadores
    [task_bcra, task_meli, task_indec] >> task_indicators


# DAG 2: Monthly ETL
with DAG(
    'mercado_automotor_monthly_etl',
    default_args=default_args,
    description='ETL mensual: ACARA + ADEFA + DNRPA',
    schedule_interval='0 8 5 * *',  # Monthly on day 5 at 8 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mercado_automotor', 'monthly', 'etl'],
) as dag_monthly:

    # ACARA scraping (mensual)
    task_acara = PythonOperator(
        task_id='scrape_acara_patentamientos',
        python_callable=scrape_acara,
    )

    # ADEFA scraping (mensual)
    task_adefa = PythonOperator(
        task_id='scrape_adefa_produccion',
        python_callable=scrape_adefa,
    )

    # DNRPA scraping (mensual) - Fuente oficial con detalle provincial
    task_dnrpa = PythonOperator(
        task_id='scrape_dnrpa_patentamientos',
        python_callable=scrape_dnrpa,
    )

    # Calculate monthly indicators
    task_monthly_indicators = PythonOperator(
        task_id='calculate_monthly_indicators',
        python_callable=calculate_indicators,
    )

    # Dependencies: ACARA, ADEFA y DNRPA en paralelo, luego calcular indicadores
    [task_acara, task_adefa, task_dnrpa] >> task_monthly_indicators


# DAG 3: Manual Full Sync
with DAG(
    'mercado_automotor_full_sync',
    default_args=default_args,
    description='Sincronización completa manual de todas las fuentes',
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mercado_automotor', 'manual', 'full_sync'],
) as dag_full_sync:

    task_sync_acara = PythonOperator(
        task_id='full_sync_acara',
        python_callable=scrape_acara,
    )

    task_sync_adefa = PythonOperator(
        task_id='full_sync_adefa',
        python_callable=scrape_adefa,
    )

    task_sync_bcra_full = PythonOperator(
        task_id='full_sync_bcra',
        python_callable=sync_bcra,
    )

    task_sync_meli_full = PythonOperator(
        task_id='full_sync_mercadolibre',
        python_callable=scrape_mercadolibre,
    )

    task_sync_indec_full = PythonOperator(
        task_id='full_sync_indec',
        python_callable=sync_indec,
    )

    task_final_indicators = PythonOperator(
        task_id='calculate_all_indicators',
        python_callable=calculate_indicators,
    )

    # All sources in parallel, then calculate indicators
    [task_sync_acara, task_sync_adefa, task_sync_bcra_full, task_sync_meli_full, task_sync_indec_full] >> task_final_indicators
