"""
DAG principal de ETL - Mercado Automotor
Orchestración de APIs y procesamiento de datos
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys

# Add backend to path
sys.path.insert(0, '/opt/airflow/backend')

from backend.api_clients import BCRAClient
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
    description='ETL diario: BCRA + Indicadores',
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

    # Calculate indicators
    task_indicators = PythonOperator(
        task_id='calculate_indicators',
        python_callable=calculate_indicators,
    )

    # Dependencies
    task_bcra >> task_indicators


# DAG 2: Manual Full Sync
with DAG(
    'mercado_automotor_full_sync',
    default_args=default_args,
    description='Sincronización completa manual: BCRA + Indicadores',
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mercado_automotor', 'manual', 'full_sync'],
) as dag_full_sync:

    task_sync_bcra_full = PythonOperator(
        task_id='full_sync_bcra',
        python_callable=sync_bcra,
    )

    task_final_indicators = PythonOperator(
        task_id='calculate_all_indicators',
        python_callable=calculate_indicators,
    )

    # BCRA sync, then calculate indicators
    task_sync_bcra_full >> task_final_indicators
