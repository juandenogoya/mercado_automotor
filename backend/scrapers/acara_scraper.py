"""
Scraper para datos de patentamientos de ACARA/FACCARA.
"""
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger

from .base_scraper import BaseScraper
from backend.config.settings import settings
from backend.models.patentamientos import Patentamiento
from backend.utils.database import get_db


class AcaraScraper(BaseScraper):
    """
    Scraper para datos de patentamientos de ACARA/FACCARA.

    Fuentes:
    - ACARA: www.acara.org.ar/estudios_economicos/estadisticas.php
    - FACCARA: www.faccara.org.ar/estadisticas-0km-usados/

    Datos obtenidos:
    - Patentamientos de 0km por marca y modelo
    - Transferencias de usados
    - Series históricas mensuales
    """

    def __init__(self):
        super().__init__(name="ACARA")
        self.base_url_faccara = settings.faccara_base_url
        self.base_url_acara = settings.acara_base_url

    def scrape(self, fecha_desde: Optional[date] = None, fecha_hasta: Optional[date] = None) -> Dict[str, Any]:
        """
        Scrapea datos de patentamientos.

        Args:
            fecha_desde: Fecha inicial (default: None = todo disponible)
            fecha_hasta: Fecha final (default: None = hasta hoy)

        Returns:
            Dictionary con datos scrapeados y metadata
        """
        logger.info(f"[{self.name}] Iniciando scraping de patentamientos...")

        try:
            # Intentar primero FACCARA (más fácil de scrapear)
            data_0km = self._scrape_faccara_0km()
            data_usados = self._scrape_faccara_usados()

            # Si FACCARA falla, intentar ACARA
            if not data_0km and not data_usados:
                logger.warning(f"[{self.name}] FACCARA no disponible, intentando ACARA...")
                data_0km, data_usados = self._scrape_acara_selenium()

            # Combinar datos
            all_data = []
            if data_0km:
                all_data.extend(data_0km)
            if data_usados:
                all_data.extend(data_usados)

            # Guardar en base de datos
            saved_count = self._save_to_database(all_data)

            result = {
                "status": "success",
                "source": self.name,
                "timestamp": datetime.utcnow(),
                "records_scraped": len(all_data),
                "records_saved": saved_count,
                "date_range": {
                    "from": min([d['fecha'] for d in all_data]) if all_data else None,
                    "to": max([d['fecha'] for d in all_data]) if all_data else None,
                }
            }

            logger.success(f"[{self.name}] ✓ Scraping completado: {saved_count} registros guardados")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] ✗ Error en scraping: {e}")
            return {
                "status": "error",
                "source": self.name,
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }

    def _scrape_faccara_0km(self) -> List[Dict[str, Any]]:
        """
        Scrapea datos de 0km desde FACCARA.
        FACCARA suele publicar tablas en HTML más fáciles de parsear.
        """
        url = f"{self.base_url_faccara}/estadisticas-0km-usados/"

        logger.info(f"[{self.name}] Scrapeando 0km desde FACCARA...")

        html = self._get_html(url)
        if not html:
            return []

        soup = self._parse_html(html)
        if not soup:
            return []

        data = []

        try:
            # Buscar tablas de patentamientos
            # NOTA: La estructura exacta depende del sitio actual
            # Este es un ejemplo genérico que debe ajustarse
            tables = soup.find_all('table', class_='estadisticas')

            for table in tables:
                # Parsear headers
                headers = [th.text.strip() for th in table.find_all('th')]

                # Parsear filas
                for row in table.find_all('tr')[1:]:  # Skip header row
                    cols = [td.text.strip() for td in row.find_all('td')]

                    if len(cols) >= 2:
                        # Ejemplo de estructura: Marca | Ene-2024 | Feb-2024 | ...
                        marca = cols[0]

                        for i, cantidad_str in enumerate(cols[1:], start=1):
                            if i < len(headers):
                                try:
                                    cantidad = int(cantidad_str.replace('.', '').replace(',', ''))
                                    periodo = headers[i]  # Ej: "Ene-2024"

                                    # Parsear periodo
                                    fecha_obj = self._parse_periodo(periodo)

                                    if fecha_obj:
                                        data.append({
                                            'fecha': fecha_obj,
                                            'anio': fecha_obj.year,
                                            'mes': fecha_obj.month,
                                            'tipo_vehiculo': '0km',
                                            'marca': marca,
                                            'cantidad': cantidad,
                                            'fuente': 'FACCARA',
                                            'periodo_reportado': fecha_obj.strftime('%Y-%m')
                                        })

                                except (ValueError, AttributeError):
                                    continue

            logger.info(f"[{self.name}] ✓ FACCARA 0km: {len(data)} registros")
            return data

        except Exception as e:
            logger.error(f"[{self.name}] Error parseando FACCARA 0km: {e}")
            return []

    def _scrape_faccara_usados(self) -> List[Dict[str, Any]]:
        """
        Scrapea datos de usados desde FACCARA.
        """
        # Similar a _scrape_faccara_0km pero para usados
        # Implementación simplificada por brevedad
        logger.info(f"[{self.name}] Scrapeando usados desde FACCARA...")

        # TODO: Implementar cuando se analice estructura real del sitio
        return []

    def _scrape_acara_selenium(self) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scrapea datos desde ACARA usando Selenium (requiere JavaScript).
        """
        url = f"{self.base_url_acara}/estudios_economicos/estadisticas.php"

        logger.info(f"[{self.name}] Scrapeando desde ACARA con Selenium...")

        try:
            driver = self._init_selenium()
            driver.get(url)

            # Esperar a que cargue la tabla
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

            # Parsear con BeautifulSoup
            html = driver.page_source
            soup = self._parse_html(html)

            # TODO: Implementar parsing según estructura real
            # Este es un placeholder

            data_0km = []
            data_usados = []

            logger.info(f"[{self.name}] ✓ ACARA: {len(data_0km)} 0km, {len(data_usados)} usados")

            return data_0km, data_usados

        except Exception as e:
            logger.error(f"[{self.name}] Error en ACARA Selenium: {e}")
            return [], []
        finally:
            self._close_selenium()

    def _parse_periodo(self, periodo_str: str) -> Optional[date]:
        """
        Parsea string de periodo a date object.

        Ejemplos:
        - "Ene-2024" -> date(2024, 1, 1)
        - "01/2024" -> date(2024, 1, 1)
        - "2024-01" -> date(2024, 1, 1)
        """
        meses_es = {
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4,
            'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
            'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }

        try:
            # Formato: "Ene-2024"
            if '-' in periodo_str:
                mes_str, anio_str = periodo_str.lower().split('-')
                mes = meses_es.get(mes_str[:3])
                anio = int(anio_str)

                if mes:
                    return date(anio, mes, 1)

            # Formato: "01/2024"
            elif '/' in periodo_str:
                mes_str, anio_str = periodo_str.split('/')
                return date(int(anio_str), int(mes_str), 1)

            # Formato: "2024-01"
            parts = periodo_str.split('-')
            if len(parts) == 2:
                return date(int(parts[0]), int(parts[1]), 1)

        except (ValueError, AttributeError) as e:
            logger.warning(f"[{self.name}] No se pudo parsear periodo: {periodo_str} - {e}")

        return None

    def _save_to_database(self, data: List[Dict[str, Any]]) -> int:
        """
        Guarda datos en la base de datos evitando duplicados.

        Returns:
            Número de registros guardados
        """
        if not data:
            return 0

        saved_count = 0

        with get_db() as db:
            for record in data:
                try:
                    # Verificar si ya existe
                    existing = db.query(Patentamiento).filter(
                        Patentamiento.fecha == record['fecha'],
                        Patentamiento.marca == record.get('marca'),
                        Patentamiento.tipo_vehiculo == record['tipo_vehiculo'],
                        Patentamiento.fuente == record['fuente']
                    ).first()

                    if not existing:
                        patentamiento = Patentamiento(**record)
                        db.add(patentamiento)
                        saved_count += 1
                    else:
                        # Actualizar cantidad si cambió
                        if existing.cantidad != record['cantidad']:
                            existing.cantidad = record['cantidad']
                            existing.updated_at = datetime.utcnow()

                except Exception as e:
                    logger.warning(f"[{self.name}] Error guardando registro: {e}")
                    continue

            db.commit()

        logger.info(f"[{self.name}] ✓ Guardados {saved_count} nuevos registros en BD")
        return saved_count


# Ejemplo de uso
if __name__ == "__main__":
    from backend.config.logger import setup_logger

    setup_logger()

    with AcaraScraper() as scraper:
        result = scraper.scrape()
        print(result)
