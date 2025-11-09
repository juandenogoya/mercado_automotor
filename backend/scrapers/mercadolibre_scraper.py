"""
Web Scraper para MercadoLibre Argentina.

Dado que la API pública fue cerrada en 2025, este scraper obtiene datos
directamente del HTML de MercadoLibre.com.ar

IMPORTANTE: Usar responsablemente, respetando términos de servicio y rate limits.
"""

from datetime import date, datetime
from typing import Dict, List, Any, Optional
import time
import random
import re
from urllib.parse import urlencode, quote_plus

import requests
from bs4 import BeautifulSoup
from loguru import logger

from backend.config.settings import settings
from backend.models.mercadolibre_listings import MercadoLibreListing
from backend.utils.database import get_db


class MercadoLibreScraperException(Exception):
    """Excepción base para errores del scraper."""
    pass


class BlockedByMercadoLibreException(MercadoLibreScraperException):
    """Excepción cuando MercadoLibre bloquea el scraping."""
    pass


class MercadoLibreScraper:
    """
    Scraper para obtener datos de vehículos desde MercadoLibre.com.ar

    Incluye:
    - Logging detallado para identificar bloqueos
    - Rotating user-agents para evitar detección
    - Rate limiting inteligente
    - Detección de CAPTCHAs y bloqueos
    - Parsing robusto de HTML
    """

    BASE_URL = "https://www.mercadolibre.com.ar"

    # User agents reales para rotar y evitar detección
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    def __init__(self):
        """Inicializa el scraper."""
        self.session = requests.Session()
        self.request_count = 0
        self.last_request_time = time.time()

        # Configurar delays para no saturar el servidor
        self.min_delay = settings.scraping_delay_min  # 3 segundos
        self.max_delay = settings.scraping_delay_max  # 7 segundos

        logger.info("[MercadoLibre Scraper] Inicializado")

    def _get_random_user_agent(self) -> str:
        """Retorna un User-Agent aleatorio."""
        return random.choice(self.USER_AGENTS)

    def _get_headers(self) -> Dict[str, str]:
        """Genera headers realistas para las requests."""
        return {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

    def _apply_rate_limit(self):
        """Aplica delay aleatorio entre requests."""
        # Calcular tiempo desde última request
        elapsed = time.time() - self.last_request_time

        # Delay aleatorio entre min y max
        delay = random.uniform(self.min_delay, self.max_delay)

        # Si no pasó suficiente tiempo, esperar
        if elapsed < delay:
            wait_time = delay - elapsed
            logger.debug(f"[Rate Limit] Esperando {wait_time:.2f}s antes de próxima request")
            time.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_count += 1

        if self.request_count % 10 == 0:
            logger.info(f"[Rate Limit] {self.request_count} requests realizadas")

    def _detect_blocking(self, response: requests.Response, html_content: str) -> bool:
        """
        Detecta si MercadoLibre está bloqueando el scraping.

        Returns:
            True si detecta bloqueo, False si todo OK
        """
        # Detectar códigos HTTP de bloqueo
        if response.status_code == 403:
            logger.error("[BLOQUEO] Status 403 Forbidden - IP o User-Agent bloqueado")
            return True

        if response.status_code == 429:
            logger.error("[BLOQUEO] Status 429 Too Many Requests - Rate limit excedido")
            return True

        if response.status_code == 503:
            logger.warning("[BLOQUEO] Status 503 Service Unavailable - Servicio temporalmente no disponible")
            return True

        # Detectar CAPTCHA en el contenido
        if 'captcha' in html_content.lower():
            logger.error("[BLOQUEO] CAPTCHA detectado en la página")
            return True

        # Detectar páginas de error de ML
        if 'ops! algo salió mal' in html_content.lower():
            logger.error("[BLOQUEO] Página de error de MercadoLibre")
            return True

        # Detectar firewall/cloudflare
        if 'cloudflare' in html_content.lower() or 'ray id' in html_content.lower():
            logger.error("[BLOQUEO] Cloudflare/Firewall detectado")
            return True

        # Detectar si no hay resultados cuando debería haberlos
        if len(html_content) < 5000:  # HTML muy corto, probablemente bloqueado
            logger.warning("[BLOQUEO POSIBLE] HTML muy corto, posible bloqueo silencioso")
            return True

        return False

    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parsea un string de precio a float."""
        try:
            # Remover $ y puntos de miles, reemplazar coma por punto
            clean = price_str.replace('$', '').replace('.', '').replace(',', '.').strip()
            return float(clean)
        except:
            return None

    def _parse_vehicle_attrs(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrae atributos del vehículo desde el HTML.

        Args:
            soup: BeautifulSoup object del item

        Returns:
            Diccionario con atributos parseados
        """
        attrs = {}

        # Intentar encontrar tabla de atributos
        # ML usa diferentes estructuras, buscar varias opciones
        attr_rows = soup.find_all('tr', class_=re.compile('.*attribute.*|.*spec.*'))

        for row in attr_rows:
            try:
                label = row.find('th')
                value = row.find('td')

                if label and value:
                    label_text = label.get_text(strip=True).lower()
                    value_text = value.get_text(strip=True)

                    # Mapear atributos
                    if 'marca' in label_text:
                        attrs['marca'] = value_text
                    elif 'modelo' in label_text:
                        attrs['modelo'] = value_text
                    elif 'año' in label_text:
                        try:
                            attrs['anio'] = int(value_text)
                        except:
                            pass
                    elif 'kilómetro' in label_text or 'km' in label_text:
                        try:
                            km_str = re.sub(r'[^\d]', '', value_text)
                            attrs['kilometros'] = int(km_str)
                        except:
                            pass
                    elif 'combustible' in label_text:
                        attrs['combustible'] = value_text
            except Exception as e:
                logger.debug(f"Error parseando atributo: {e}")
                continue

        return attrs

    def search_vehicles(
        self,
        query: Optional[str] = None,
        marca: Optional[str] = None,
        modelo: Optional[str] = None,
        condition: Optional[str] = None,  # 'new' o 'used'
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """
        Busca vehículos en MercadoLibre mediante web scraping.

        Args:
            query: Búsqueda libre (ej: "Toyota Hilux")
            marca: Marca específica
            modelo: Modelo específico
            condition: 'new' (0km) o 'used' (usado)
            max_pages: Máximo de páginas a scrapear

        Returns:
            Dict con resultados y metadata
        """
        logger.info(f"[Búsqueda] Iniciando scraping: query={query}, marca={marca}, modelo={modelo}, condition={condition}")

        # Construir query de búsqueda
        search_terms = []
        if query:
            search_terms.append(query)
        if marca:
            search_terms.append(marca)
        if modelo:
            search_terms.append(modelo)

        search_query = ' '.join(search_terms) if search_terms else 'auto'

        # Construir URL de búsqueda usando el formato correcto de MercadoLibre
        # MercadoLibre usa: /vehiculos/autos-camionetas-y-4x4/{busqueda}

        # URL base para vehículos
        base_search_url = f"https://listado.mercadolibre.com.ar/vehiculos/autos-camionetas-y-4x4"

        # Parámetros de búsqueda
        params = {}

        # Agregar búsqueda al path o como parámetro
        if search_query and search_query != 'auto':
            # Usar el query en la URL directamente
            search_url_base = f"{base_search_url}/{quote_plus(search_query.lower())}"
        else:
            search_url_base = base_search_url

        # Condición (0km o usado)
        if condition:
            if condition == 'new':
                params['ITEM_CONDITION'] = '2230284'  # Nuevo
            else:
                params['ITEM_CONDITION'] = '2230581'  # Usado

        items = []
        page = 1

        while page <= max_pages:
            try:
                # URL con paginación
                # MercadoLibre usa _Desde_{offset} o _NoIndex_True para paginación
                offset = (page - 1) * 48 + 1  # ML usa páginas de 48 items

                if page == 1:
                    search_url = search_url_base
                else:
                    search_url = f"{search_url_base}_Desde_{offset}"

                if params:
                    search_url += "?" + urlencode(params)

                logger.info(f"[Página {page}] Scrapeando: {search_url}")

                # Aplicar rate limiting
                self._apply_rate_limit()

                # Realizar request
                response = self.session.get(
                    search_url,
                    headers=self._get_headers(),
                    timeout=30
                )

                # Verificar status HTTP
                if response.status_code == 404:
                    logger.error(f"[Página {page}] Status 404 - URL no encontrada")
                    logger.error(f"[URL Incorrecta] Verificar construcción de URL: {search_url}")
                    break

                # Verificar bloqueo
                if self._detect_blocking(response, response.text):
                    logger.error(f"[BLOQUEADO] Scraping bloqueado en página {page}")
                    raise BlockedByMercadoLibreException(
                        f"MercadoLibre bloqueó el scraping. Revisar logs para detalles."
                    )

                logger.success(f"[Página {page}] Status {response.status_code} - OK")

                # Parsear HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Encontrar items de vehículos
                # ML usa diferentes selectores, probar varios
                item_containers = []

                # Opción 1: clase ui-search-layout__item (estructura nueva)
                item_containers = soup.find_all('li', class_=re.compile('.*ui-search-layout__item.*'))

                # Opción 2: clase ui-search-result (estructura antigua)
                if not item_containers:
                    item_containers = soup.find_all('li', class_=re.compile('.*ui-search-result.*'))

                # Opción 3: div con clase específica de items
                if not item_containers:
                    item_containers = soup.find_all('div', class_=re.compile('.*andes-card.*ui-search-result.*'))

                # Opción 4: buscar por estructura - ol > li con link a /MLA
                if not item_containers:
                    all_items = soup.find_all('li')
                    item_containers = [item for item in all_items if item.find('a', href=re.compile(r'/MLA'))]

                if not item_containers:
                    logger.warning(f"[Página {page}] No se encontraron items")
                    logger.debug(f"[HTML Debug] Primeros 500 caracteres: {response.text[:500]}")

                    # Intentar detectar si es una página válida
                    if 'mercado' not in response.text.lower():
                        logger.error("[Página Inválida] No parece ser una página de MercadoLibre")

                    break

                logger.info(f"[Página {page}] Encontrados {len(item_containers)} items")

                # Parsear cada item
                for container in item_containers:
                    try:
                        item_data = self._parse_item(container)
                        if item_data:
                            items.append(item_data)
                    except Exception as e:
                        logger.debug(f"Error parseando item: {e}")
                        continue

                page += 1

            except BlockedByMercadoLibreException:
                raise
            except Exception as e:
                logger.error(f"[Error Página {page}] {e}")
                break

        logger.info(f"[Resultado] Total items scrapeados: {len(items)}")

        return {
            'status': 'success',
            'total_scraped': len(items),
            'pages_scraped': page - 1,
            'items': items
        }

    def _parse_item(self, container: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Parsea un item individual de vehículo.

        Args:
            container: BeautifulSoup object del contenedor del item

        Returns:
            Dict con datos del item o None si falla
        """
        try:
            item = {}

            # Título
            title_elem = container.find('h2', class_=re.compile('.*title.*'))
            if title_elem:
                item['title'] = title_elem.get_text(strip=True)
            else:
                return None

            # Precio
            price_elem = container.find('span', class_=re.compile('.*price-tag-amount.*'))
            if price_elem:
                price_str = price_elem.get_text(strip=True)
                item['price'] = self._parse_price(price_str)

            # URL del item
            link_elem = container.find('a', href=True)
            if link_elem:
                item['url'] = link_elem['href']

                # Extraer ID del item desde la URL
                id_match = re.search(r'MLA-?(\d+)', item['url'])
                if id_match:
                    item['meli_id'] = f"MLA{id_match.group(1)}"

            # Ubicación
            location_elem = container.find('span', class_=re.compile('.*location.*'))
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                item['location'] = location_text

                # Intentar separar provincia/ciudad
                if ',' in location_text:
                    parts = location_text.split(',')
                    item['ciudad'] = parts[0].strip()
                    if len(parts) > 1:
                        item['provincia'] = parts[1].strip()

            # Condición (0km o usado) - inferir del título
            title_lower = item.get('title', '').lower()
            if '0km' in title_lower or '0 km' in title_lower:
                item['condicion'] = 'new'
            else:
                item['condicion'] = 'used'

            # Intentar extraer marca/modelo del título
            # Común ver: "MARCA MODELO AÑO ..."
            title_parts = item['title'].split()
            if len(title_parts) >= 2:
                item['marca'] = title_parts[0]
                item['modelo'] = ' '.join(title_parts[1:3])  # Tomar 2 palabras para modelo

            # Año - buscar patrón de 4 dígitos
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', item['title'])
            if year_match:
                item['anio'] = int(year_match.group(1))

            # Fecha del snapshot
            item['fecha_snapshot'] = date.today()

            return item

        except Exception as e:
            logger.debug(f"Error parseando item: {e}")
            return None

    def save_to_database(self, items: List[Dict[str, Any]]) -> int:
        """
        Guarda items scrapeados en la base de datos.

        Args:
            items: Lista de items scrapeados

        Returns:
            Número de items guardados
        """
        if not items:
            logger.warning("[BD] No hay items para guardar")
            return 0

        saved_count = 0

        with get_db() as db:
            for item in items:
                try:
                    # Verificar si ya existe (mismo ID y fecha)
                    existing = db.query(MercadoLibreListing).filter(
                        MercadoLibreListing.meli_id == item.get('meli_id'),
                        MercadoLibreListing.fecha_snapshot == item.get('fecha_snapshot')
                    ).first()

                    if existing:
                        logger.debug(f"[BD] Item {item.get('meli_id')} ya existe para hoy")
                        continue

                    # Crear nuevo registro
                    listing = MercadoLibreListing(
                        meli_id=item.get('meli_id'),
                        fecha_snapshot=item.get('fecha_snapshot'),
                        marca=item.get('marca'),
                        modelo=item.get('modelo'),
                        anio=item.get('anio'),
                        kilometros=item.get('kilometros'),
                        combustible=item.get('combustible'),
                        precio=item.get('price'),
                        moneda='ARS',
                        provincia=item.get('provincia'),
                        ciudad=item.get('ciudad'),
                        estado='active',
                        condicion=item.get('condicion'),
                        titulo=item.get('title'),
                        url=item.get('url'),
                        es_nuevo=item.get('condicion') == 'new'
                    )

                    db.add(listing)
                    saved_count += 1

                except Exception as e:
                    logger.error(f"[BD] Error guardando item: {e}")
                    continue

            db.commit()
            logger.success(f"[BD] Guardados {saved_count} items nuevos")

        return saved_count

    def scrape_and_save(
        self,
        marcas: Optional[List[str]] = None,
        max_items_per_marca: int = 100
    ) -> Dict[str, Any]:
        """
        Scrapea vehículos y los guarda automáticamente en la BD.

        Args:
            marcas: Lista de marcas a scrapear (None = todas)
            max_items_per_marca: Máximo items por marca

        Returns:
            Dict con estadísticas del scraping
        """
        if not marcas:
            # Marcas principales del mercado argentino
            marcas = [
                'Toyota', 'Ford', 'Volkswagen', 'Chevrolet', 'Fiat',
                'Renault', 'Peugeot', 'Nissan', 'Honda', 'Jeep'
            ]

        all_items = []
        total_saved = 0

        for marca in marcas:
            logger.info(f"[Marca] Procesando: {marca}")

            try:
                # Calcular páginas necesarias (50 items por página)
                max_pages = min(5, (max_items_per_marca // 50) + 1)

                result = self.search_vehicles(
                    marca=marca,
                    max_pages=max_pages
                )

                if result['status'] == 'success':
                    items = result['items'][:max_items_per_marca]
                    all_items.extend(items)

                    # Guardar en BD
                    saved = self.save_to_database(items)
                    total_saved += saved

                    logger.success(f"[Marca] {marca}: {len(items)} items scrapeados, {saved} guardados")
                else:
                    logger.warning(f"[Marca] {marca}: Error en scraping")

            except BlockedByMercadoLibreException as e:
                logger.error(f"[BLOQUEADO] Deteniendo scraping: {e}")
                break
            except Exception as e:
                logger.error(f"[Error] {marca}: {e}")
                continue

        return {
            'status': 'completed' if not isinstance(e, BlockedByMercadoLibreException) else 'blocked',
            'total_scraped': len(all_items),
            'total_saved': total_saved,
            'marcas_procesadas': len(marcas),
            'fecha': datetime.now()
        }
