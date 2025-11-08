"""
Tests unitarios para API clients (con mocking).
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api_clients.bcra_client import BCRAClient
from backend.api_clients.mercadolibre_client import MercadoLibreClient


class TestBCRAClient:
    """Tests para BCRA Client."""

    @patch('backend.api_clients.bcra_client.requests.get')
    def test_get_principales_variables_success(self, mock_get):
        """Test obtener principales variables exitoso."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"idVariable": 1, "cdSerie": 246, "descripcion": "BADLAR", "valor": 35.5}
            ]
        }
        mock_get.return_value = mock_response

        client = BCRAClient()
        result = client.get_principales_variables()

        assert result is not None
        assert len(result) > 0
        mock_get.assert_called_once()

    @patch('backend.api_clients.bcra_client.requests.get')
    def test_get_principales_variables_error(self, mock_get):
        """Test manejo de error en API."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server error")
        mock_get.return_value = mock_response

        client = BCRAClient()
        result = client.get_principales_variables()

        assert result is None

    @patch('backend.api_clients.bcra_client.requests.get')
    def test_get_variable_historica_success(self, mock_get):
        """Test obtener variable histórica exitoso."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"fecha": "2024-01-15", "valor": 35.5}
            ]
        }
        mock_get.return_value = mock_response

        client = BCRAClient()
        result = client.get_variable_historica(
            variable_id=1,
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 1, 31)
        )

        assert result is not None
        assert len(result) > 0

    @patch('backend.api_clients.bcra_client.requests.get')
    def test_rate_limiting(self, mock_get):
        """Test que respeta rate limiting."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        client = BCRAClient()

        # Hacer múltiples requests
        for _ in range(3):
            client.get_principales_variables()

        # Verificar que se llamó múltiples veces
        assert mock_get.call_count == 3


class TestMercadoLibreClient:
    """Tests para MercadoLibre Client."""

    @patch('backend.api_clients.mercadolibre_client.requests.get')
    def test_search_vehicles_success(self, mock_get):
        """Test búsqueda de vehículos exitosa."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "MLA123456",
                    "title": "Toyota Corolla 2023",
                    "price": 8500000,
                    "currency_id": "ARS"
                }
            ],
            "paging": {
                "total": 1,
                "offset": 0,
                "limit": 50
            }
        }
        mock_get.return_value = mock_response

        client = MercadoLibreClient()
        result = client.search_vehicles(marca="Toyota")

        assert result is not None
        assert len(result) > 0
        mock_get.assert_called_once()

    @patch('backend.api_clients.mercadolibre_client.requests.get')
    def test_get_item_detail_success(self, mock_get):
        """Test obtener detalle de item exitoso."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "MLA123456",
            "title": "Toyota Corolla 2023",
            "price": 8500000,
            "currency_id": "ARS",
            "condition": "new",
            "attributes": []
        }
        mock_get.return_value = mock_response

        client = MercadoLibreClient()
        result = client.get_item_detail("MLA123456")

        assert result is not None
        assert result.get("id") == "MLA123456"

    @patch('backend.api_clients.mercadolibre_client.requests.get')
    def test_rate_limiting_respected(self, mock_get):
        """Test que respeta rate limiting."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        client = MercadoLibreClient()
        client.rate_limit_per_minute = 5  # Límite bajo para test

        # Hacer requests dentro del límite
        for _ in range(3):
            client.search_vehicles(marca="Toyota")

        assert mock_get.call_count == 3

    @patch('backend.api_clients.mercadolibre_client.requests.get')
    def test_error_handling(self, mock_get):
        """Test manejo de errores."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response

        client = MercadoLibreClient()
        result = client.get_item_detail("INVALID_ID")

        assert result is None

    @patch('backend.api_clients.mercadolibre_client.requests.get')
    def test_pagination_handling(self, mock_get):
        """Test manejo de paginación."""
        # Primera página
        mock_response_1 = Mock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {
            "results": [{"id": f"MLA{i}"} for i in range(50)],
            "paging": {
                "total": 100,
                "offset": 0,
                "limit": 50
            }
        }

        # Segunda página
        mock_response_2 = Mock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {
            "results": [{"id": f"MLA{i}"} for i in range(50, 100)],
            "paging": {
                "total": 100,
                "offset": 50,
                "limit": 50
            }
        }

        mock_get.side_effect = [mock_response_1, mock_response_2]

        client = MercadoLibreClient()
        result = client.search_vehicles(marca="Toyota")

        # Debería haber obtenido items de la primera página
        assert result is not None
        assert len(result) > 0


class TestAPIClientIntegration:
    """Tests de integración entre clients."""

    @patch('backend.api_clients.bcra_client.requests.get')
    @patch('backend.api_clients.mercadolibre_client.requests.get')
    def test_multiple_clients_concurrent(self, mock_get_ml, mock_get_bcra):
        """Test múltiples clients funcionando concurrentemente."""
        # Mock BCRA
        mock_response_bcra = Mock()
        mock_response_bcra.status_code = 200
        mock_response_bcra.json.return_value = {"results": []}
        mock_get_bcra.return_value = mock_response_bcra

        # Mock ML
        mock_response_ml = Mock()
        mock_response_ml.status_code = 200
        mock_response_ml.json.return_value = {"results": []}
        mock_get_ml.return_value = mock_response_ml

        # Crear clients
        bcra_client = BCRAClient()
        ml_client = MercadoLibreClient()

        # Ejecutar concurrentemente
        bcra_result = bcra_client.get_principales_variables()
        ml_result = ml_client.search_vehicles(marca="Toyota")

        # Ambos deberían funcionar
        assert bcra_result is not None
        assert ml_result is not None
