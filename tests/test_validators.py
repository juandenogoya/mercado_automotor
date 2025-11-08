"""
Tests para validadores Pydantic de datos scrapeados.
"""
import pytest
from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scrapers.validators import (
    PatentamientoData,
    ProduccionData,
    BCRAIndicadorData,
    MercadoLibreListingData,
    validate_data
)


class TestPatentamientoValidator:
    """Tests para validador de patentamientos."""

    def test_patentamiento_valid(self, sample_patentamiento_data):
        """Test con datos válidos."""
        validated = PatentamientoData(**sample_patentamiento_data)
        assert validated.marca == 'Toyota'
        assert validated.cantidad == 5000
        assert validated.tipo_vehiculo == '0km'

    def test_patentamiento_invalid_tipo(self, sample_patentamiento_data):
        """Test con tipo de vehículo inválido."""
        data = sample_patentamiento_data.copy()
        data['tipo_vehiculo'] = 'seminuevo'

        with pytest.raises(ValueError, match="tipo_vehiculo debe ser uno de"):
            PatentamientoData(**data)

    def test_patentamiento_invalid_fuente(self, sample_patentamiento_data):
        """Test con fuente inválida."""
        data = sample_patentamiento_data.copy()
        data['fuente'] = 'INVALID'

        with pytest.raises(ValueError, match="fuente debe ser uno de"):
            PatentamientoData(**data)

    def test_patentamiento_fecha_futura(self, sample_patentamiento_data):
        """Test con fecha futura."""
        data = sample_patentamiento_data.copy()
        data['fecha'] = date.today() + timedelta(days=30)
        data['anio'] = 2025

        with pytest.raises(ValueError, match="fecha no puede ser futura"):
            PatentamientoData(**data)

    def test_patentamiento_cantidad_negativa(self, sample_patentamiento_data):
        """Test con cantidad negativa."""
        data = sample_patentamiento_data.copy()
        data['cantidad'] = -100

        with pytest.raises(ValueError):
            PatentamientoData(**data)

    def test_patentamiento_marca_normalizacion(self, sample_patentamiento_data):
        """Test normalización de marca."""
        data = sample_patentamiento_data.copy()
        data['marca'] = '  toyota  '

        validated = PatentamientoData(**data)
        assert validated.marca == 'Toyota'


class TestProduccionValidator:
    """Tests para validador de producción."""

    def test_produccion_valid(self, sample_produccion_data):
        """Test con datos válidos."""
        validated = ProduccionData(**sample_produccion_data)
        assert validated.terminal == 'Toyota'
        assert validated.unidades_producidas == 15000
        assert validated.unidades_exportadas == 5000

    def test_produccion_invalid_fuente(self, sample_produccion_data):
        """Test con fuente inválida."""
        data = sample_produccion_data.copy()
        data['fuente'] = 'INVALID'

        with pytest.raises(ValueError, match="fuente debe ser 'ADEFA'"):
            ProduccionData(**data)

    def test_produccion_exportadas_mayor_producidas(self, sample_produccion_data):
        """Test con exportadas > producidas (debería generar warning pero validar)."""
        data = sample_produccion_data.copy()
        data['unidades_producidas'] = 5000
        data['unidades_exportadas'] = 15000

        # Debería validar pero generar warning
        validated = ProduccionData(**data)
        assert validated.unidades_exportadas == 15000

    def test_produccion_valores_negativos(self, sample_produccion_data):
        """Test con valores negativos."""
        data = sample_produccion_data.copy()
        data['unidades_producidas'] = -100

        with pytest.raises(ValueError):
            ProduccionData(**data)


class TestBCRAIndicadorValidator:
    """Tests para validador de indicadores BCRA."""

    def test_bcra_valid(self, sample_bcra_data):
        """Test con datos válidos."""
        validated = BCRAIndicadorData(**sample_bcra_data)
        assert validated.indicador == 'BADLAR'
        assert validated.valor == 35.5

    def test_bcra_tasa_fuera_de_rango(self, sample_bcra_data):
        """Test con tasa fuera de rango."""
        data = sample_bcra_data.copy()
        data['valor'] = 600.0  # >500%

        with pytest.raises(ValueError, match="Tasa fuera de rango"):
            BCRAIndicadorData(**data)

    def test_bcra_tasa_negativa(self, sample_bcra_data):
        """Test con tasa negativa."""
        data = sample_bcra_data.copy()
        data['valor'] = -10.0

        with pytest.raises(ValueError, match="Tasa fuera de rango"):
            BCRAIndicadorData(**data)

    def test_bcra_fecha_futura(self, sample_bcra_data):
        """Test con fecha futura."""
        data = sample_bcra_data.copy()
        data['fecha'] = date.today() + timedelta(days=1)

        with pytest.raises(ValueError, match="fecha no puede ser futura"):
            BCRAIndicadorData(**data)


class TestMercadoLibreValidator:
    """Tests para validador de MercadoLibre."""

    def test_meli_valid(self, sample_meli_data):
        """Test con datos válidos."""
        validated = MercadoLibreListingData(**sample_meli_data)
        assert validated.meli_id == 'MLA123456789'
        assert validated.marca == 'Toyota'
        assert validated.precio == 8500000.0

    def test_meli_invalid_id(self, sample_meli_data):
        """Test con ID inválido."""
        data = sample_meli_data.copy()
        data['meli_id'] = 'INVALID'

        with pytest.raises(ValueError, match="meli_id inválido"):
            MercadoLibreListingData(**data)

    def test_meli_invalid_moneda(self, sample_meli_data):
        """Test con moneda inválida."""
        data = sample_meli_data.copy()
        data['moneda'] = 'EUR'

        with pytest.raises(ValueError, match="moneda debe ser una de"):
            MercadoLibreListingData(**data)

    def test_meli_invalid_condicion(self, sample_meli_data):
        """Test con condición inválida."""
        data = sample_meli_data.copy()
        data['condicion'] = 'seminuevo'

        with pytest.raises(ValueError, match="condicion debe ser una de"):
            MercadoLibreListingData(**data)

    def test_meli_precio_negativo(self, sample_meli_data):
        """Test con precio negativo."""
        data = sample_meli_data.copy()
        data['precio'] = -1000

        with pytest.raises(ValueError):
            MercadoLibreListingData(**data)

    def test_meli_anio_futuro(self, sample_meli_data):
        """Test con año futuro."""
        data = sample_meli_data.copy()
        data['anio'] = 2030

        with pytest.raises(ValueError):
            MercadoLibreListingData(**data)


class TestValidateDataFunction:
    """Tests para función validate_data."""

    def test_validate_all_valid(self):
        """Test con todos los datos válidos."""
        data_list = [
            {
                'fecha': date(2024, 1, 15),
                'anio': 2024,
                'mes': 1,
                'tipo_vehiculo': '0km',
                'marca': 'Toyota',
                'cantidad': 5000,
                'fuente': 'ACARA',
                'periodo_reportado': '2024-01'
            },
            {
                'fecha': date(2024, 1, 15),
                'anio': 2024,
                'mes': 1,
                'tipo_vehiculo': 'usado',
                'marca': 'Ford',
                'cantidad': 3000,
                'fuente': 'FACCARA',
                'periodo_reportado': '2024-01'
            }
        ]

        valid_data, invalid_data = validate_data(data_list, PatentamientoData)

        assert len(valid_data) == 2
        assert len(invalid_data) == 0

    def test_validate_mixed(self):
        """Test con datos válidos e inválidos."""
        data_list = [
            {
                'fecha': date(2024, 1, 15),
                'anio': 2024,
                'mes': 1,
                'tipo_vehiculo': '0km',
                'marca': 'Toyota',
                'cantidad': 5000,
                'fuente': 'ACARA',
                'periodo_reportado': '2024-01'
            },
            {
                'fecha': date(2024, 1, 15),
                'anio': 2024,
                'mes': 1,
                'tipo_vehiculo': 'INVALID',  # Inválido
                'marca': 'Ford',
                'cantidad': 3000,
                'fuente': 'ACARA',
                'periodo_reportado': '2024-01'
            }
        ]

        valid_data, invalid_data = validate_data(data_list, PatentamientoData)

        assert len(valid_data) == 1
        assert len(invalid_data) == 1
        assert 'error' in invalid_data[0]

    def test_validate_all_invalid(self):
        """Test con todos los datos inválidos."""
        data_list = [
            {
                'fecha': date(2024, 1, 15),
                'tipo_vehiculo': 'INVALID',
                'marca': 'Toyota',
                'cantidad': -100,
                'fuente': 'WRONG'
            }
        ]

        valid_data, invalid_data = validate_data(data_list, PatentamientoData)

        assert len(valid_data) == 0
        assert len(invalid_data) == 1
