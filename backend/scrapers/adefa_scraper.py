"""
Scraper para datos de producción de ADEFA.
"""
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import re
import pandas as pd
from pathlib import Path
from loguru import logger

from .base_scraper import BaseScraper
from backend.config.settings import settings
from backend.models.produccion import Produccion
from backend.utils.database import get_db


class AdefaScraper(BaseScraper):
    """
    Scraper para datos de producción de ADEFA.

    Fuente: www.adefa.org.ar/es/estadisticas-mensuales

    Datos obtenidos:
    - Producción nacional por terminal
    - Exportaciones por terminal
    - Series históricas mensuales

    NOTA: ADEFA publica datos en formatos variables (PDF, Excel, HTML).
    Este scraper debe ser flexible para manejar diferentes formatos.
    """

    def __init__(self):
        super().__init__(name="ADEFA")
        self.base_url = settings.adefa_base_url
        self.stats_url = f"{self.base_url}/es/estadisticas-mensuales"

    def scrape(self, fecha_desde: Optional[date] = None, fecha_hasta: Optional[date] = None) -> Dict[str, Any]:
        """
        Scrapea datos de producción.

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final

        Returns:
            Dictionary con datos scrapeados y metadata
        """
        logger.info(f"[{self.name}] Iniciando scraping de producción...")

        try:
            # Obtener listado de archivos/reportes disponibles
            reportes = self._get_reportes_disponibles()

            if not reportes:
                logger.warning(f"[{self.name}] No se encontraron reportes disponibles")
                return {
                    "status": "warning",
                    "source": self.name,
                    "timestamp": datetime.utcnow(),
                    "message": "No se encontraron reportes disponibles"
                }

            # Scrapear cada reporte
            all_data = []
            for reporte in reportes:
                data = self._scrape_reporte(reporte)
                if data:
                    all_data.extend(data)

            # Guardar en base de datos
            saved_count = self._save_to_database(all_data)

            result = {
                "status": "success",
                "source": self.name,
                "timestamp": datetime.utcnow(),
                "records_scraped": len(all_data),
                "records_saved": saved_count,
                "reportes_procesados": len(reportes),
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

    def _get_reportes_disponibles(self) -> List[Dict[str, str]]:
        """
        Obtiene el listado de reportes mensuales disponibles en el sitio.

        Returns:
            Lista de dictionaries con info de cada reporte: {url, periodo, formato}
        """
        logger.info(f"[{self.name}] Buscando reportes disponibles...")

        html = self._get_html(self.stats_url)
        if not html:
            return []

        soup = self._parse_html(html)
        if not soup:
            return []

        reportes = []

        try:
            # Buscar enlaces a archivos PDF/Excel
            # La estructura exacta depende del sitio
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                text = link.text.strip()

                # Filtrar solo links de estadísticas mensuales
                if any(ext in href.lower() for ext in ['.pdf', '.xlsx', '.xls']):
                    # Intentar extraer periodo del nombre/texto
                    periodo = self._extract_periodo(text + ' ' + href)

                    if periodo:
                        # Construir URL absoluta si es relativa
                        if not href.startswith('http'):
                            href = f"{self.base_url}{href}" if href.startswith('/') else f"{self.stats_url}/{href}"

                        formato = 'pdf' if '.pdf' in href.lower() else 'excel'

                        reportes.append({
                            'url': href,
                            'periodo': periodo,
                            'formato': formato,
                            'texto': text
                        })

            logger.info(f"[{self.name}] ✓ Encontrados {len(reportes)} reportes")

            # Ordenar por periodo (más recientes primero)
            reportes.sort(key=lambda x: x['periodo'], reverse=True)

            return reportes

        except Exception as e:
            logger.error(f"[{self.name}] Error obteniendo reportes: {e}")
            return []

    def _extract_periodo(self, text: str) -> Optional[str]:
        """
        Extrae periodo (YYYY-MM) de un texto.

        Ejemplos:
        - "Estadísticas Enero 2024" -> "2024-01"
        - "produccion_2024_01.pdf" -> "2024-01"
        - "reporte-03-2024.xlsx" -> "2024-03"
        """
        meses_es = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }

        try:
            # Patrón 1: "YYYY-MM" o "YYYY_MM"
            match = re.search(r'(\d{4})[-_](\d{2})', text)
            if match:
                return f"{match.group(1)}-{match.group(2)}"

            # Patrón 2: "MM-YYYY" o "MM_YYYY"
            match = re.search(r'(\d{2})[-_](\d{4})', text)
            if match:
                return f"{match.group(2)}-{match.group(1)}"

            # Patrón 3: "Mes YYYY" (español)
            text_lower = text.lower()
            for mes_nombre, mes_num in meses_es.items():
                if mes_nombre in text_lower:
                    match = re.search(r'\d{4}', text)
                    if match:
                        return f"{match.group(0)}-{mes_num}"

        except Exception as e:
            logger.debug(f"[{self.name}] Error extrayendo periodo de '{text}': {e}")

        return None

    def _scrape_reporte(self, reporte: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Scrapea un reporte individual.

        Args:
            reporte: Dict con info del reporte

        Returns:
            Lista de registros de producción
        """
        logger.info(f"[{self.name}] Scrapeando reporte: {reporte['periodo']} ({reporte['formato']})")

        self._sleep()  # Rate limiting

        try:
            if reporte['formato'] == 'pdf':
                return self._scrape_pdf(reporte)
            elif reporte['formato'] == 'excel':
                return self._scrape_excel(reporte)
            else:
                logger.warning(f"[{self.name}] Formato no soportado: {reporte['formato']}")
                return []

        except Exception as e:
            logger.error(f"[{self.name}] Error scrapeando reporte {reporte['periodo']}: {e}")
            return []

    def _scrape_pdf(self, reporte: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extrae datos de un PDF usando pdfplumber.
        """
        import pdfplumber

        logger.info(f"[{self.name}] Extrayendo datos de PDF: {reporte['url']}")

        try:
            # Descargar PDF
            response = self.session.get(reporte['url'], timeout=settings.scraping_timeout)
            response.raise_for_status()

            # Guardar temporalmente
            temp_path = Path(settings.data_raw_path) / f"adefa_{reporte['periodo']}.pdf"
            temp_path.parent.mkdir(parents=True, exist_ok=True)

            with open(temp_path, 'wb') as f:
                f.write(response.content)

            # Extraer tablas con pdfplumber
            data = []

            with pdfplumber.open(temp_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()

                    for table in tables:
                        # Parsear tabla (estructura específica de ADEFA)
                        parsed_data = self._parse_table_adefa(table, reporte['periodo'])
                        data.extend(parsed_data)

            logger.info(f"[{self.name}] ✓ Extraídos {len(data)} registros del PDF")
            return data

        except Exception as e:
            logger.error(f"[{self.name}] Error procesando PDF: {e}")
            return []

    def _scrape_excel(self, reporte: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extrae datos de un archivo Excel.
        """
        logger.info(f"[{self.name}] Extrayendo datos de Excel: {reporte['url']}")

        try:
            # Leer Excel directamente con pandas
            df = pd.read_excel(reporte['url'])

            # Parsear DataFrame
            data = self._parse_dataframe_adefa(df, reporte['periodo'])

            logger.info(f"[{self.name}] ✓ Extraídos {len(data)} registros del Excel")
            return data

        except Exception as e:
            logger.error(f"[{self.name}] Error procesando Excel: {e}")
            return []

    def _parse_table_adefa(self, table: List[List[str]], periodo: str) -> List[Dict[str, Any]]:
        """
        Parsea una tabla extraída de PDF de ADEFA.

        NOTA: La estructura exacta debe adaptarse según el formato real de ADEFA.
        """
        data = []

        try:
            # Ejemplo de estructura esperada:
            # Terminal | Producción | Exportación
            # Toyota   | 15000      | 5000
            # Ford     | 12000      | 3000

            for row in table[1:]:  # Skip header
                if len(row) >= 2:
                    terminal = row[0]
                    produccion_str = row[1] if len(row) > 1 else '0'
                    exportacion_str = row[2] if len(row) > 2 else '0'

                    # Limpiar y convertir a int
                    produccion = int(re.sub(r'[^\d]', '', produccion_str or '0') or 0)
                    exportacion = int(re.sub(r'[^\d]', '', exportacion_str or '0') or 0)

                    # Parsear periodo a fecha
                    anio, mes = periodo.split('-')
                    fecha_obj = date(int(anio), int(mes), 1)

                    data.append({
                        'fecha': fecha_obj,
                        'anio': int(anio),
                        'mes': int(mes),
                        'terminal': terminal,
                        'unidades_producidas': produccion,
                        'unidades_exportadas': exportacion,
                        'fuente': 'ADEFA',
                        'periodo_reportado': periodo
                    })

        except Exception as e:
            logger.warning(f"[{self.name}] Error parseando tabla: {e}")

        return data

    def _parse_dataframe_adefa(self, df: pd.DataFrame, periodo: str) -> List[Dict[str, Any]]:
        """
        Parsea DataFrame de Excel de ADEFA.
        """
        data = []

        try:
            # Adaptar según estructura real del Excel
            anio, mes = periodo.split('-')
            fecha_obj = date(int(anio), int(mes), 1)

            for _, row in df.iterrows():
                # Ejemplo genérico
                data.append({
                    'fecha': fecha_obj,
                    'anio': int(anio),
                    'mes': int(mes),
                    'terminal': row.get('Terminal') or row.get('Marca'),
                    'unidades_producidas': int(row.get('Producción', 0)),
                    'unidades_exportadas': int(row.get('Exportación', 0)),
                    'fuente': 'ADEFA',
                    'periodo_reportado': periodo
                })

        except Exception as e:
            logger.warning(f"[{self.name}] Error parseando DataFrame: {e}")

        return data

    def _save_to_database(self, data: List[Dict[str, Any]]) -> int:
        """
        Guarda datos en la base de datos evitando duplicados.
        """
        if not data:
            return 0

        saved_count = 0

        with get_db() as db:
            for record in data:
                try:
                    # Verificar si ya existe
                    existing = db.query(Produccion).filter(
                        Produccion.fecha == record['fecha'],
                        Produccion.terminal == record.get('terminal'),
                        Produccion.fuente == record['fuente']
                    ).first()

                    if not existing:
                        produccion = Produccion(**record)
                        db.add(produccion)
                        saved_count += 1
                    else:
                        # Actualizar si cambió
                        if (existing.unidades_producidas != record['unidades_producidas'] or
                            existing.unidades_exportadas != record['unidades_exportadas']):
                            existing.unidades_producidas = record['unidades_producidas']
                            existing.unidades_exportadas = record['unidades_exportadas']
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

    with AdefaScraper() as scraper:
        result = scraper.scrape()
        print(result)
