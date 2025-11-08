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

from backend.scrapers import AcaraScraper, AdefaScraper
from backend.api_clients import BCRAClient, MercadoLibreClient
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


def calculate_indicators():
    """Task: Calculate derived indicators."""
    logger.info("Calculating indicators...")

    # TODO: Implement indicator calculation logic
    # - Índice de tensión de demanda
    # - Rotación de stock
    # - Accesibilidad de compra
    # - Ranking de atención

    logger.info("Indicator calculation completed")
    return {"status": "success"}


# ==================== DAG DEFINITIONS ====================

# DAG 1: Daily ETL
with DAG(
    'mercado_automotor_daily_etl',
    default_args=default_args,
    description='ETL diario: BCRA + MercadoLibre',
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

    # Calculate indicators
    task_indicators = PythonOperator(
        task_id='calculate_indicators',
        python_callable=calculate_indicators,
    )

    # Dependencies
    [task_bcra, task_meli] >> task_indicators


# DAG 2: Monthly ETL
with DAG(
    'mercado_automotor_monthly_etl',
    default_args=default_args,
    description='ETL mensual: ACARA + ADEFA',
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

    # Calculate monthly indicators
    task_monthly_indicators = PythonOperator(
        task_id='calculate_monthly_indicators',
        python_callable=calculate_indicators,
    )

    # Dependencies
    [task_acara, task_adefa] >> task_monthly_indicators


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

    task_final_indicators = PythonOperator(
        task_id='calculate_all_indicators',
        python_callable=calculate_indicators,
    )

    # All sources in parallel, then calculate indicators
    [task_sync_acara, task_sync_adefa, task_sync_bcra_full, task_sync_meli_full] >> task_final_indicators
