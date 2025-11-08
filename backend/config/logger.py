"""
Configuración centralizada de logging usando loguru.
"""
import sys
from pathlib import Path
from loguru import logger
from .settings import settings


def setup_logger():
    """
    Configura el logger global de la aplicación.
    """
    # Remover handlers por defecto
    logger.remove()

    # Console handler con formato colorizado
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )

    # File handler con rotación
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="100 MB",
        retention="30 days",
        compression="zip"
    )

    # Handler específico para errores
    logger.add(
        log_path.parent / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="50 MB",
        retention="90 days",
        compression="zip"
    )

    logger.info(f"Logger configurado - Nivel: {settings.log_level}")
    return logger


# Inicializar logger
setup_logger()
