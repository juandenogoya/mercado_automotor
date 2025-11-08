"""
Base scraper class con funcionalidades comunes.
"""
import time
import random
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger

from backend.config.settings import settings


class BaseScraper(ABC):
    """
    Clase base para todos los scrapers.
    Implementa funcionalidades comunes: rate limiting, retries, logging, etc.
    """

    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.scraping_user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self._driver: Optional[webdriver.Chrome] = None

    def _sleep(self):
        """Sleep random time entre requests para respetar rate limiting."""
        delay = random.uniform(settings.scraping_delay_min, settings.scraping_delay_max)
        logger.debug(f"[{self.name}] Esperando {delay:.2f} segundos...")
        time.sleep(delay)

    def _get_html(self, url: str, max_retries: int = None) -> Optional[str]:
        """
        Obtiene el HTML de una URL con manejo de errores y retries.

        Args:
            url: URL a scrapear
            max_retries: Número máximo de reintentos

        Returns:
            HTML como string o None si falla
        """
        max_retries = max_retries or settings.scraping_max_retries

        for attempt in range(max_retries):
            try:
                logger.info(f"[{self.name}] Obteniendo: {url} (intento {attempt + 1}/{max_retries})")
                response = self.session.get(
                    url,
                    timeout=settings.scraping_timeout
                )
                response.raise_for_status()

                logger.success(f"[{self.name}] ✓ Descargado correctamente: {url}")
                return response.text

            except requests.RequestException as e:
                logger.warning(f"[{self.name}] Error en intento {attempt + 1}: {e}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"[{self.name}] Reintentando en {wait_time} segundos...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"[{self.name}] ✗ Falló después de {max_retries} intentos: {url}")
                    return None

        return None

    def _parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """
        Parsea HTML usando BeautifulSoup.

        Args:
            html: HTML como string

        Returns:
            BeautifulSoup object o None si falla
        """
        try:
            return BeautifulSoup(html, 'lxml')
        except Exception as e:
            logger.error(f"[{self.name}] Error al parsear HTML: {e}")
            return None

    def _init_selenium(self) -> webdriver.Chrome:
        """
        Inicializa Selenium WebDriver para sitios con JavaScript.

        Returns:
            WebDriver instance
        """
        if self._driver is not None:
            return self._driver

        logger.info(f"[{self.name}] Inicializando Selenium WebDriver...")

        chrome_options = Options()

        if settings.headless_browser:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'user-agent={settings.scraping_user_agent}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            if settings.chrome_driver_path == "auto":
                service = Service(ChromeDriverManager().install())
            else:
                service = Service(settings.chrome_driver_path)

            self._driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.success(f"[{self.name}] ✓ Selenium WebDriver inicializado")

            return self._driver

        except Exception as e:
            logger.error(f"[{self.name}] Error al inicializar Selenium: {e}")
            raise

    def _close_selenium(self):
        """Cierra Selenium WebDriver."""
        if self._driver is not None:
            logger.info(f"[{self.name}] Cerrando Selenium WebDriver...")
            self._driver.quit()
            self._driver = None

    def close(self):
        """Limpia recursos."""
        self.session.close()
        self._close_selenium()
        logger.info(f"[{self.name}] Scraper cerrado")

    @abstractmethod
    def scrape(self) -> Dict[str, Any]:
        """
        Método principal de scraping. Debe ser implementado por cada scraper.

        Returns:
            Dictionary con los datos scrapeados
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
