"""
Cliente para API de MercadoLibre.

API Documentation:
- https://developers.mercadolibre.com.ar/
- Base URL: https://api.mercadolibre.com
- Sitio Argentina: MLA
- Categoría Autos: MLA1743
"""
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import requests
import time
from loguru import logger

from backend.config.settings import settings
from backend.models.mercadolibre_listings import MercadoLibreListing
from backend.utils.database import get_db


class MercadoLibreClient:
    """
    Cliente para interactuar con la API de MercadoLibre.

    Endpoints principales:
    - /sites/{SITE_ID}/search: Búsqueda de productos
    - /items/{ITEM_ID}: Detalle de un item
    - /categories/{CATEGORY_ID}: Información de categoría
    """

    # Configuración de MercadoLibre Argentina
    SITE_ID = "MLA"
    CATEGORIA_AUTOS = "MLA1743"  # Autos, Motos y Otros

    # Subcategorías relevantes
    CATEGORIA_AUTOS_0KM = "MLA1744"
    CATEGORIA_AUTOS_USADOS = "MLA80109"

    def __init__(self):
        self.base_url = "https://api.mercadolibre.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
        })
        # Deshabilitar verificación SSL para desarrollo en Windows
        self.session.verify = False
        # Suprimir warnings de SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Rate limiting
        self.requests_count = 0
        self.last_request_time = time.time()
        self.max_requests_per_minute = settings.mercadolibre_rate_limit

    def _wait_rate_limit(self):
        """
        Implementa rate limiting para respetar límites de la API.
        """
        self.requests_count += 1

        # Resetear contador cada minuto
        if time.time() - self.last_request_time > 60:
            self.requests_count = 0
            self.last_request_time = time.time()

        # Si excedemos el límite, esperar
        if self.requests_count >= self.max_requests_per_minute:
            wait_time = 60 - (time.time() - self.last_request_time)
            if wait_time > 0:
                logger.warning(f"[MercadoLibre] Rate limit alcanzado, esperando {wait_time:.0f}s...")
                time.sleep(wait_time)
                self.requests_count = 0
                self.last_request_time = time.time()

    def search_vehicles(
        self,
        marca: Optional[str] = None,
        modelo: Optional[str] = None,
        anio_desde: Optional[int] = None,
        anio_hasta: Optional[int] = None,
        condicion: Optional[str] = None,  # 'new' o 'used'
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Busca vehículos en MercadoLibre.

        Args:
            marca: Marca del vehículo
            modelo: Modelo del vehículo
            anio_desde: Año mínimo
            anio_hasta: Año máximo
            condicion: 'new' (0km) o 'used' (usado)
            limit: Resultados por página (max 50)
            offset: Offset para paginación

        Returns:
            Dict con resultados de búsqueda
        """
        self._wait_rate_limit()

        url = f"{self.base_url}/sites/{self.SITE_ID}/search"

        # Construir parámetros de búsqueda
        params = {
            'category': self.CATEGORIA_AUTOS,
            'limit': min(limit, 50),  # MercadoLibre limita a 50
            'offset': offset
        }

        # Query string para marca/modelo
        query_parts = []
        if marca:
            query_parts.append(marca)
        if modelo:
            query_parts.append(modelo)

        if query_parts:
            params['q'] = ' '.join(query_parts)

        # Filtros
        if condicion:
            params['condition'] = condicion

        # Año (usando atributos)
        if anio_desde or anio_hasta:
            # VEHICLE_YEAR es el ID del atributo de año
            if anio_desde:
                params['VEHICLE_YEAR_from'] = anio_desde
            if anio_hasta:
                params['VEHICLE_YEAR_to'] = anio_hasta

        logger.info(f"[MercadoLibre] Buscando vehículos: {params}")

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            logger.success(f"[MercadoLibre] ✓ Encontrados {data['paging']['total']} resultados")

            return {
                "status": "success",
                "total": data['paging']['total'],
                "limit": data['paging']['limit'],
                "offset": data['paging']['offset'],
                "results": data['results']
            }

        except requests.RequestException as e:
            logger.error(f"[MercadoLibre] Error en búsqueda: {e}")
            return {
                "status": "error",
                "error": str(e),
                "results": []
            }

    def get_item_detail(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene detalle completo de un item.

        Args:
            item_id: ID del item (ej: "MLA123456789")

        Returns:
            Dict con detalle del item o None si falla
        """
        self._wait_rate_limit()

        url = f"{self.base_url}/items/{item_id}"

        logger.debug(f"[MercadoLibre] Obteniendo detalle: {item_id}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            logger.error(f"[MercadoLibre] Error obteniendo item {item_id}: {e}")
            return None

    def scrape_market_snapshot(
        self,
        marcas: Optional[List[str]] = None,
        max_items_por_marca: int = 100
    ) -> Dict[str, Any]:
        """
        Genera un snapshot del mercado actual en MercadoLibre.

        Args:
            marcas: Lista de marcas a scrapear (None = todas)
            max_items_por_marca: Máximo items a obtener por marca

        Returns:
            Dict con resumen del scraping
        """
        logger.info(f"[MercadoLibre] Iniciando snapshot del mercado...")

        # Marcas principales del mercado argentino
        if not marcas:
            marcas = [
                'Toyota', 'Ford', 'Volkswagen', 'Chevrolet', 'Fiat',
                'Renault', 'Peugeot', 'Nissan', 'Honda', 'Jeep',
                'RAM', 'Citroen', 'Mercedes-Benz', 'BMW', 'Audi'
            ]

        all_items = []
        fecha_hoy = date.today()

        for marca in marcas:
            logger.info(f"[MercadoLibre] Procesando marca: {marca}")

            # Obtener listados de la marca (0km y usados)
            items_marca = []

            # Paginar resultados
            offset = 0
            while len(items_marca) < max_items_por_marca:
                result = self.search_vehicles(
                    marca=marca,
                    limit=50,
                    offset=offset
                )

                if result['status'] != 'success' or not result['results']:
                    break

                items_marca.extend(result['results'])
                offset += 50

                # Si no hay más resultados
                if offset >= result['total']:
                    break

            # Procesar items
            for item in items_marca[:max_items_por_marca]:
                # Extraer información relevante
                processed_item = self._process_item(item, fecha_hoy)
                if processed_item:
                    all_items.append(processed_item)

            logger.info(f"[MercadoLibre] ✓ {marca}: {len(items_marca)} items procesados")

        # Guardar en base de datos
        saved_count = self._save_items_to_db(all_items)

        result = {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "fecha_snapshot": fecha_hoy,
            "marcas_procesadas": len(marcas),
            "items_scraped": len(all_items),
            "items_saved": saved_count
        }

        logger.success(f"[MercadoLibre] ✓ Snapshot completado: {saved_count} items guardados")

        return result

    def _process_item(self, item: Dict[str, Any], fecha_snapshot: date) -> Optional[Dict[str, Any]]:
        """
        Procesa un item de MercadoLibre para extraer información relevante.
        """
        try:
            # Extraer atributos del vehículo
            attributes = {attr['id']: attr for attr in item.get('attributes', [])}

            marca = attributes.get('BRAND', {}).get('value_name')
            modelo = attributes.get('MODEL', {}).get('value_name')
            anio = attributes.get('VEHICLE_YEAR', {}).get('value_name')
            kilometros = attributes.get('KILOMETERS', {}).get('value_name')
            combustible = attributes.get('FUEL_TYPE', {}).get('value_name')

            # Ubicación
            location = item.get('location', {})
            provincia = location.get('state', {}).get('name')
            ciudad = location.get('city', {}).get('name')

            processed = {
                'meli_id': item['id'],
                'fecha_snapshot': fecha_snapshot,
                'marca': marca,
                'modelo': modelo,
                'anio': int(anio) if anio and str(anio).isdigit() else None,
                'kilometros': int(kilometros) if kilometros and str(kilometros).replace('.', '').isdigit() else None,
                'combustible': combustible,
                'precio': float(item['price']),
                'moneda': item['currency_id'],
                'provincia': provincia,
                'ciudad': ciudad,
                'estado': item['status'],
                'condicion': item['condition'],
                'titulo': item['title'],
                'url': item['permalink'],
                'es_nuevo': item['condition'] == 'new'
            }

            return processed

        except Exception as e:
            logger.warning(f"[MercadoLibre] Error procesando item {item.get('id')}: {e}")
            return None

    def _save_items_to_db(self, items: List[Dict[str, Any]]) -> int:
        """
        Guarda items en la base de datos.
        """
        if not items:
            return 0

        saved_count = 0

        with get_db() as db:
            for item in items:
                try:
                    # Verificar si ya existe este snapshot
                    existing = db.query(MercadoLibreListing).filter(
                        MercadoLibreListing.meli_id == item['meli_id'],
                        MercadoLibreListing.fecha_snapshot == item['fecha_snapshot']
                    ).first()

                    if not existing:
                        listing = MercadoLibreListing(**item)
                        db.add(listing)
                        saved_count += 1
                    else:
                        # Actualizar precio si cambió
                        if float(existing.precio) != item['precio']:
                            existing.precio = item['precio']
                            existing.estado = item['estado']
                            existing.updated_at = datetime.utcnow()

                except Exception as e:
                    logger.warning(f"[MercadoLibre] Error guardando item {item.get('meli_id')}: {e}")
                    continue

            db.commit()

        logger.info(f"[MercadoLibre] ✓ Guardados {saved_count} nuevos items en BD")
        return saved_count

    def get_trending_models(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene los modelos más buscados/listados.

        Args:
            top_n: Número de modelos a retornar

        Returns:
            Lista de modelos ordenados por cantidad de listados
        """
        logger.info(f"[MercadoLibre] Obteniendo top {top_n} modelos...")

        result = self.search_vehicles(limit=1)  # Solo para obtener tendencias

        # TODO: Implementar análisis de tendencias
        # Esto requeriría hacer múltiples queries o usar datos históricos de la BD

        return []


# Ejemplo de uso
if __name__ == "__main__":
    from backend.config.logger import setup_logger

    setup_logger()

    client = MercadoLibreClient()

    # Test 1: Búsqueda simple
    result = client.search_vehicles(marca="Toyota", condicion="new", limit=10)
    print(f"Resultados Toyota 0km: {result['total']}")

    # Test 2: Snapshot del mercado (solo 2 marcas para prueba)
    result = client.scrape_market_snapshot(
        marcas=["Toyota", "Ford"],
        max_items_por_marca=20
    )
    print("Snapshot:", result)
