"""
Utilidades para manejo de base de datos.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
from loguru import logger

from backend.config.settings import settings
from backend.models.base import Base


# Engine global
engine = create_engine(
    settings.get_database_url_sync(),
    poolclass=QueuePool,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    echo=settings.is_development,  # Log SQL queries en development
)

# SessionLocal factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """
    Inicializa la base de datos creando todas las tablas.
    """
    logger.info("Inicializando base de datos...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.success("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar base de datos: {e}")
        raise


def drop_db():
    """
    ADVERTENCIA: Elimina todas las tablas de la base de datos.
    Solo usar en desarrollo.
    """
    if settings.is_production:
        raise RuntimeError("No se puede ejecutar drop_db en producción")

    logger.warning("Eliminando todas las tablas...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.success("Tablas eliminadas correctamente")
    except Exception as e:
        logger.error(f"Error al eliminar tablas: {e}")
        raise


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager para obtener una sesión de base de datos.

    Uso:
        with get_db() as db:
            db.query(Model).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Dependency para FastAPI.

    Uso en FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db_session)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
