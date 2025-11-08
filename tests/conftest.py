"""
Pytest fixtures compartidos para todos los tests.
"""
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.base import Base
from backend.config.settings import settings


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    # Usar base de datos en memoria para tests
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create database session for tests."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def sample_fecha():
    """Fecha de ejemplo para tests."""
    return date(2024, 1, 15)


@pytest.fixture
def sample_fecha_rango():
    """Rango de fechas para tests."""
    fecha_hasta = date(2024, 1, 31)
    fecha_desde = fecha_hasta - timedelta(days=30)
    return fecha_desde, fecha_hasta


@pytest.fixture
def sample_patentamiento_data():
    """Datos de ejemplo para patentamiento."""
    return {
        'fecha': date(2024, 1, 15),
        'anio': 2024,
        'mes': 1,
        'tipo_vehiculo': '0km',
        'marca': 'Toyota',
        'cantidad': 5000,
        'fuente': 'ACARA',
        'periodo_reportado': '2024-01'
    }


@pytest.fixture
def sample_produccion_data():
    """Datos de ejemplo para producción."""
    return {
        'fecha': date(2024, 1, 15),
        'anio': 2024,
        'mes': 1,
        'terminal': 'Toyota',
        'unidades_producidas': 15000,
        'unidades_exportadas': 5000,
        'fuente': 'ADEFA',
        'periodo_reportado': '2024-01'
    }


@pytest.fixture
def sample_bcra_data():
    """Datos de ejemplo para indicadores BCRA."""
    return {
        'fecha': date(2024, 1, 15),
        'indicador': 'BADLAR',
        'valor': 35.5,
        'unidad': '%'
    }


@pytest.fixture
def sample_meli_data():
    """Datos de ejemplo para MercadoLibre."""
    return {
        'meli_id': 'MLA123456789',
        'marca': 'Toyota',
        'modelo': 'Corolla',
        'anio': 2023,
        'precio': 8500000.0,
        'moneda': 'ARS',
        'condicion': 'new',
        'kilometros': 0,
        'combustible': 'nafta',
        'transmision': 'automatica',
        'ubicacion': 'Capital Federal',
        'url': 'https://www.mercadolibre.com.ar/...',
        'fecha_snapshot': date(2024, 1, 15)
    }
