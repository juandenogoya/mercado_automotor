"""
Script de gestión del proyecto Mercado Automotor
Facilita tareas comunes de desarrollo y deployment
"""
import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.config.logger import setup_logger
from backend.config.settings import settings
from loguru import logger

setup_logger()


def init_db():
    """Inicializa la base de datos."""
    from backend.utils.database import init_db as _init_db

    logger.info("Inicializando base de datos...")
    try:
        _init_db()
        logger.success("✓ Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"✗ Error inicializando base de datos: {e}")
        sys.exit(1)


def drop_db():
    """Elimina todas las tablas (solo en desarrollo)."""
    from backend.utils.database import drop_db as _drop_db

    if settings.is_production:
        logger.error("✗ No se puede ejecutar drop_db en producción")
        sys.exit(1)

    confirm = input("⚠️  ¿Estás seguro de eliminar todas las tablas? (yes/no): ")
    if confirm.lower() != "yes":
        logger.info("Operación cancelada")
        return

    logger.warning("Eliminando todas las tablas...")
    try:
        _drop_db()
        logger.success("✓ Tablas eliminadas correctamente")
    except Exception as e:
        logger.error(f"✗ Error eliminando tablas: {e}")
        sys.exit(1)


def run_scrapers(source: str = "all"):
    """Ejecuta scrapers."""
    from backend.scrapers import AcaraScraper, AdefaScraper
    from backend.api_clients import BCRAClient, MercadoLibreClient

    logger.info(f"Ejecutando scrapers: {source}")

    if source in ["all", "acara"]:
        logger.info("Ejecutando ACARA scraper...")
        try:
            with AcaraScraper() as scraper:
                result = scraper.scrape()
                logger.info(f"ACARA result: {result}")
        except Exception as e:
            logger.error(f"ACARA error: {e}")

    if source in ["all", "adefa"]:
        logger.info("Ejecutando ADEFA scraper...")
        try:
            with AdefaScraper() as scraper:
                result = scraper.scrape()
                logger.info(f"ADEFA result: {result}")
        except Exception as e:
            logger.error(f"ADEFA error: {e}")

    if source in ["all", "bcra"]:
        logger.info("Ejecutando BCRA sync...")
        try:
            client = BCRAClient()
            result = client.sync_all_indicators()
            logger.info(f"BCRA result: {result}")
        except Exception as e:
            logger.error(f"BCRA error: {e}")

    if source in ["all", "mercadolibre", "meli"]:
        logger.info("Ejecutando MercadoLibre scraper...")
        try:
            client = MercadoLibreClient()
            result = client.scrape_market_snapshot()
            logger.info(f"MercadoLibre result: {result}")
        except Exception as e:
            logger.error(f"MercadoLibre error: {e}")

    logger.success("✓ Scrapers ejecutados")


def run_api():
    """Ejecuta la API FastAPI."""
    import uvicorn
    from backend.main import app

    logger.info("Iniciando API FastAPI...")
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )


def run_dashboard():
    """Ejecuta el dashboard Streamlit."""
    import subprocess

    logger.info("Iniciando dashboard Streamlit...")
    subprocess.run([
        "streamlit", "run", "frontend/app.py",
        "--server.port", str(settings.streamlit_server_port),
        "--server.address", settings.streamlit_server_address
    ])


def show_stats():
    """Muestra estadísticas de la base de datos."""
    from backend.utils.database import get_db
    from backend.models import Patentamiento, Produccion, BCRAIndicador, MercadoLibreListing

    logger.info("Obteniendo estadísticas de la base de datos...")

    with get_db() as db:
        stats = {
            "Patentamientos": db.query(Patentamiento).count(),
            "Producción": db.query(Produccion).count(),
            "BCRA Indicadores": db.query(BCRAIndicador).count(),
            "MercadoLibre Listings": db.query(MercadoLibreListing).count(),
        }

    logger.info("📊 Estadísticas de la base de datos:")
    for table, count in stats.items():
        logger.info(f"  - {table}: {count:,} registros")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Script de gestión del proyecto Mercado Automotor"
    )

    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # init-db
    subparsers.add_parser("init-db", help="Inicializar base de datos")

    # drop-db
    subparsers.add_parser("drop-db", help="Eliminar todas las tablas (solo dev)")

    # run-scrapers
    parser_scrapers = subparsers.add_parser("run-scrapers", help="Ejecutar scrapers")
    parser_scrapers.add_argument(
        "--source",
        choices=["all", "acara", "adefa", "bcra", "mercadolibre", "meli"],
        default="all",
        help="Fuente a scrapear"
    )

    # run-api
    subparsers.add_parser("run-api", help="Ejecutar API FastAPI")

    # run-dashboard
    subparsers.add_parser("run-dashboard", help="Ejecutar dashboard Streamlit")

    # stats
    subparsers.add_parser("stats", help="Mostrar estadísticas de la BD")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
    elif args.command == "drop-db":
        drop_db()
    elif args.command == "run-scrapers":
        run_scrapers(args.source)
    elif args.command == "run-api":
        run_api()
    elif args.command == "run-dashboard":
        run_dashboard()
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
