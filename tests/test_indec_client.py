"""
Tests para cliente INDEC (con mocking).
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api_clients.indec_client import INDECClient


class TestINDECClient:
    """Tests para INDEC Client."""

    def test_client_initialization(self):
        """Test inicialización del cliente."""
        client = INDECClient()

        assert client.api_base_url == "https://apis.datos.gob.ar/series/api"
        assert client.indec_ftp_base == "https://www.indec.gob.ar/ftp/cuadros/economia"
        assert client.session is not None

    @patch('backend.api_clients.indec_client.requests.Session.get')
    def test_get_series_success(self, mock_get):
        """Test obtener serie exitosa."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                ["2024-01-01", 150.5],
                ["2024-02-01", 152.3]
            ]
        }
        mock_get.return_value = mock_response

        client = INDECClient()
        result = client.get_series(series_id='148.3_INIVELNAL_DICI_M_26')

        assert result is not None
        assert 'data' in result
        assert len(result['data']) == 2
        mock_get.assert_called_once()

    @patch('backend.api_clients.indec_client.requests.Session.get')
    def test_get_series_error(self, mock_get):
        """Test manejo de error en API."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server error")
        mock_get.return_value = mock_response

        client = INDECClient()
        result = client.get_series(series_id='invalid')

        assert result is None

    @patch('backend.api_clients.indec_client.requests.Session.get')
    def test_get_ipc_success(self, mock_get):
        """Test obtener IPC exitoso."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                ["2024-01-01", 150.5],
                ["2024-02-01", 152.3],
                ["2024-03-01", 155.0]
            ]
        }
        mock_get.return_value = mock_response

        client = INDECClient()
        result = client.get_ipc(
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 3, 31),
            categoria='nacional'
        )

        assert result is not None
        assert len(result) == 3
        assert result[0]['indicador'] == 'ipc_nacional'
        assert result[0]['fecha'] == date(2024, 1, 1)
        assert result[0]['valor'] == 150.5

    @patch('backend.api_clients.indec_client.requests.Session.get')
    def test_get_salario_promedio_success(self, mock_get):
        """Test obtener salario promedio exitoso."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                ["2024-01-01", 300.0],  # Índice base 100
                ["2024-02-01", 310.0],
                ["2024-03-01", 320.0]
            ]
        }
        mock_get.return_value = mock_response

        client = INDECClient()
        result = client.get_salario_promedio()

        assert result is not None
        assert isinstance(result, float)
        assert result > 0

    @patch('backend.api_clients.indec_client.requests.Session.get')
    def test_get_patentamientos_excel_success(self, mock_get):
        """Test descargar Excel de patentamientos."""
        # Mock Excel response
        import io
        import pandas as pd

        # Crear un Excel simple en memoria
        excel_buffer = io.BytesIO()
        df = pd.DataFrame({
            'Fecha': ['2024-01', '2024-02'],
            'Total': [10000, 11000]
        })
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = excel_buffer.getvalue()
        mock_get.return_value = mock_response

        client = INDECClient()
        result = client.get_patentamientos_excel()

        assert result is not None
        assert isinstance(result, pd.DataFrame)

    @patch('backend.api_clients.indec_client.requests.Session.get')
    def test_sync_ipc_with_mock_db(self, mock_get):
        """Test sincronización de IPC (requiere mock de DB)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                ["2024-01-01", 150.5]
            ]
        }
        mock_get.return_value = mock_response

        client = INDECClient()

        # Nota: Este test requiere mock de la BD para funcionar completamente
        # Por ahora solo verificamos que el método existe y no falla
        assert hasattr(client, 'sync_ipc')
        assert callable(client.sync_ipc)

    def test_series_ids_configuration(self):
        """Test que los IDs de series estén configurados."""
        assert 'ipc_nacional' in INDECClient.SERIES_IDS
        assert 'ipc_alimentos' in INDECClient.SERIES_IDS
        assert 'salario_indice' in INDECClient.SERIES_IDS

        # Verificar formato de IDs
        for key, series_id in INDECClient.SERIES_IDS.items():
            assert isinstance(series_id, str)
            assert len(series_id) > 0

    @patch('backend.api_clients.indec_client.requests.Session.get')
    def test_date_range_parameters(self, mock_get):
        """Test parámetros de rango de fechas."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = INDECClient()
        client.get_series(
            series_id='test_id',
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 12, 31)
        )

        # Verificar que se pasaron los parámetros correctos
        call_args = mock_get.call_args
        params = call_args[1]['params']

        assert 'start_date' in params
        assert 'end_date' in params
        assert params['start_date'] == '2024-01-01'
        assert params['end_date'] == '2024-12-31'

    @patch('backend.api_clients.indec_client.requests.Session.get')
    def test_sync_all_indicators(self, mock_get):
        """Test sincronización de todos los indicadores."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [["2024-01-01", 150.0]]
        }
        mock_get.return_value = mock_response

        client = INDECClient()

        # Verificar que el método existe
        assert hasattr(client, 'sync_all_indicators')
        assert callable(client.sync_all_indicators)

    def test_error_handling_graceful(self):
        """Test que los errores se manejan gracefully."""
        client = INDECClient()

        # Test con series_id None (debería manejarlo)
        with patch('backend.api_clients.indec_client.requests.Session.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            result = client.get_series(series_id='test')
            assert result is None  # No debería romper

    @patch('backend.api_clients.indec_client.requests.Session.get')
    def test_csv_format_support(self, mock_get):
        """Test soporte de formato CSV."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "fecha,valor\n2024-01-01,150.5"
        mock_get.return_value = mock_response

        client = INDECClient()
        result = client.get_series(series_id='test_id', formato='csv')

        assert result is not None
        assert 'data' in result
        assert isinstance(result['data'], str)


class TestINDECIntegration:
    """Tests de integración del cliente INDEC."""

    def test_client_can_be_imported(self):
        """Test que el cliente se puede importar."""
        from backend.api_clients import INDECClient
        assert INDECClient is not None

    def test_client_instantiation(self):
        """Test que el cliente se puede instanciar."""
        client = INDECClient()
        assert client is not None
        assert hasattr(client, 'get_series')
        assert hasattr(client, 'get_ipc')
        assert hasattr(client, 'get_salario_promedio')
        assert hasattr(client, 'sync_all_indicators')

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.skip(reason="Requiere conexión a API real del INDEC")
    def test_real_api_connection(self):
        """Test conexión real a API del INDEC (solo para testing manual)."""
        client = INDECClient()

        # Intentar obtener IPC de último mes
        ipc_data = client.get_ipc(
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 1, 31),
            categoria='nacional'
        )

        # Si la API está disponible, debería retornar datos
        if ipc_data is not None:
            assert len(ipc_data) > 0
            assert all('indicador' in d for d in ipc_data)
            assert all('valor' in d for d in ipc_data)


# Markers para pytest
"""
Ejecutar tests:

# Todos los tests
pytest tests/test_indec_client.py -v

# Solo tests rápidos (sin integration)
pytest tests/test_indec_client.py -v -m "not slow"

# Con output detallado
pytest tests/test_indec_client.py -v -s
"""
