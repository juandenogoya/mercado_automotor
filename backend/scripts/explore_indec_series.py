"""
Script para explorar y validar series del INDEC en la API de datos.gob.ar

Funcionalidades:
- Buscar series por término
- Validar IDs de series existentes
- Descubrir nuevas series útiles
- Probar consultas reales
"""
import requests
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
import json
from loguru import logger


class INDECSeriesExplorer:
    """Explorador de series de tiempo del INDEC."""

    def __init__(self):
        """Inicializar explorador."""
        self.api_base = "https://apis.datos.gob.ar/series/api"
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})

    def search_series(self, query: str, source: str = "INDEC") -> List[Dict[str, Any]]:
        """
        Busca series por término.

        Args:
            query: Término de búsqueda (ej: "IPC", "salario", "EMAE")
            source: Fuente de datos (default: "INDEC")

        Returns:
            Lista de series encontradas
        """
        url = f"{self.api_base}/search"

        params = {
            'q': query,
            'source': source,
            'limit': 50
        }

        try:
            logger.info(f"Buscando series: '{query}'...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # La respuesta puede tener diferentes estructuras
            if isinstance(data, dict):
                results = data.get('data', data.get('results', []))
            else:
                results = data

            logger.success(f"✓ Encontradas {len(results)} series")
            return results

        except Exception as e:
            logger.error(f"Error buscando series: {e}")
            return []

    def validate_series(self, series_id: str) -> Optional[Dict[str, Any]]:
        """
        Valida un ID de serie consultando la API.

        Args:
            series_id: ID de la serie a validar

        Returns:
            Metadatos de la serie o None si no existe
        """
        url = f"{self.api_base}/series"

        params = {
            'ids': series_id,
            'metadata': 'full'
        }

        try:
            logger.info(f"Validando serie: {series_id}...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            logger.success(f"✓ Serie válida: {series_id}")

            return data

        except Exception as e:
            logger.error(f"✗ Serie inválida o no accesible: {series_id} - {e}")
            return None

    def get_series_data(
        self,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> Optional[List]:
        """
        Obtiene datos de una serie.

        Args:
            series_id: ID de la serie
            start_date: Fecha inicial
            end_date: Fecha final
            limit: Límite de resultados

        Returns:
            Datos de la serie
        """
        url = f"{self.api_base}/series"

        params = {
            'ids': series_id,
            'limit': limit
        }

        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()

        try:
            logger.info(f"Obteniendo datos de: {series_id}...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            series_data = data.get('data', [])

            logger.success(f"✓ Obtenidos {len(series_data)} puntos de datos")
            return series_data

        except Exception as e:
            logger.error(f"Error obteniendo datos: {e}")
            return None

    def discover_indec_series(self) -> Dict[str, List[Dict]]:
        """
        Descubre series útiles del INDEC.

        Returns:
            Dict con categorías de series descubiertas
        """
        logger.info("=== Descubriendo series del INDEC ===\n")

        categories = {
            'ipc': ['IPC', 'índice de precios', 'inflación'],
            'salarios': ['salario', 'índice de salarios', 'remuneración'],
            'actividad': ['EMAE', 'actividad económica', 'PIB'],
            'empleo': ['desempleo', 'empleo', 'tasa de desocupación'],
            'produccion': ['IPI', 'producción industrial', 'industria'],
            'comercio': ['comercio', 'ventas'],
            'construccion': ['construcción', 'ISAC', 'actividad construcción']
        }

        discovered = {}

        for category, queries in categories.items():
            logger.info(f"\n--- Categoría: {category.upper()} ---")
            category_results = []

            for query in queries:
                results = self.search_series(query)

                for result in results[:3]:  # Top 3 por query
                    # Extraer info relevante
                    if isinstance(result, dict):
                        series_info = {
                            'id': result.get('id', 'N/A'),
                            'title': result.get('title', result.get('description', 'N/A')),
                            'source': result.get('source', 'N/A'),
                            'frequency': result.get('frequency', 'N/A')
                        }
                        category_results.append(series_info)

                        logger.info(f"  • {series_info['title'][:60]}...")
                        logger.info(f"    ID: {series_info['id']}")

            discovered[category] = category_results

        return discovered


def main():
    """Función principal de exploración."""
    from backend.config.logger import setup_logger
    setup_logger()

    explorer = INDECSeriesExplorer()

    print("\n" + "="*70)
    print("  EXPLORADOR DE SERIES DEL INDEC")
    print("="*70 + "\n")

    # 1. Validar IDs existentes en el código
    print("1. VALIDANDO IDs EXISTENTES\n")

    existing_ids = {
        'IPC Nacional': '148.3_INIVELNAL_DICI_M_26',
        'IPC Alimentos': '148.3_INALIBED_DICI_M_29',
        'Salario Índice': '11.3_ISAC_0_M_18',
    }

    valid_ids = {}
    for name, series_id in existing_ids.items():
        result = explorer.validate_series(series_id)
        if result:
            valid_ids[name] = series_id
            print(f"✓ {name}: VÁLIDO")

            # Obtener muestra de datos
            data = explorer.get_series_data(series_id, limit=5)
            if data:
                print(f"  Últimos datos: {data[-3:]}\n")
        else:
            print(f"✗ {name}: INVÁLIDO o no accesible\n")

    # 2. Descubrir nuevas series
    print("\n2. DESCUBRIENDO NUEVAS SERIES\n")

    discovered = explorer.discover_indec_series()

    # 3. Resumen
    print("\n" + "="*70)
    print("  RESUMEN")
    print("="*70)
    print(f"\nSeries validadas: {len(valid_ids)}/{len(existing_ids)}")

    total_discovered = sum(len(series) for series in discovered.values())
    print(f"Series descubiertas: {total_discovered}")

    # 4. Generar reporte JSON
    report = {
        'timestamp': date.today().isoformat(),
        'validated_series': valid_ids,
        'discovered_series': discovered
    }

    report_path = 'indec_series_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReporte guardado en: {report_path}")

    # 5. Sugerencias
    print("\n" + "="*70)
    print("  SERIES SUGERIDAS PARA AGREGAR")
    print("="*70 + "\n")

    print("Basado en el descubrimiento, considera agregar:")
    print("- EMAE (Actividad Económica): Para correlacionar con ventas")
    print("- Tasa de Desempleo: Afecta poder adquisitivo")
    print("- IPI (Producción Industrial): Complementa datos de ADEFA")
    print("- Indicadores de Comercio: Tendencias de consumo")


if __name__ == "__main__":
    main()
