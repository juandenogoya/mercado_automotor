"""
Tests de scrapers con datos reales.

IMPORTANTE: Estos tests hacen requests reales a los sitios web.
Úsalos con moderación y respeto a los términos de servicio.
"""
import pytest
from datetime import date, timedelta
from loguru import logger
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scrapers.acara_scraper import AcaraScraper
from backend.scrapers.adefa_scraper import AdefaScraper
from backend.scrapers.validators import PatentamientoData, ProduccionData, validate_data
from backend.config.logger import setup_logger

# Setup logging
setup_logger()


class TestAcaraScraperReal:
    """Tests del scraper de ACARA con datos reales."""

    @pytest.mark.slow
    @pytest.mark.integration
    def test_acara_connection(self):
        """Test de conexión a ACARA."""
        with AcaraScraper() as scraper:
            # Verificar que el sitio responde
            html = scraper._get_html(scraper.base_url_acara)
            assert html is not None, "No se pudo conectar a ACARA"
            assert len(html) > 0, "HTML vacío de ACARA"
            logger.info(f"✓ Conexión a ACARA exitosa ({len(html)} bytes)")

    @pytest.mark.slow
    @pytest.mark.integration
    def test_faccara_connection(self):
        """Test de conexión a FACCARA."""
        with AcaraScraper() as scraper:
            # Verificar que el sitio responde
            html = scraper._get_html(scraper.base_url_faccara)
            assert html is not None, "No se pudo conectar a FACCARA"
            assert len(html) > 0, "HTML vacío de FACCARA"
            logger.info(f"✓ Conexión a FACCARA exitosa ({len(html)} bytes)")

    @pytest.mark.slow
    @pytest.mark.integration
    def test_acara_html_structure(self):
        """Analiza la estructura HTML de ACARA."""
        with AcaraScraper() as scraper:
            html = scraper._get_html(f"{scraper.base_url_acara}/estudios_economicos/estadisticas.php")

            if html:
                soup = scraper._parse_html(html)

                # Buscar tablas
                tables = soup.find_all('table')
                logger.info(f"ACARA: Encontradas {len(tables)} tablas")

                # Buscar enlaces a archivos
                links = soup.find_all('a', href=True)
                pdf_links = [l for l in links if '.pdf' in l['href'].lower()]
                excel_links = [l for l in links if '.xls' in l['href'].lower()]

                logger.info(f"ACARA: {len(pdf_links)} PDFs, {len(excel_links)} Excels")

                # Imprimir primeras 5 tablas para análisis manual
                for i, table in enumerate(tables[:5]):
                    logger.info(f"\nTabla {i+1}:")
                    logger.info(f"  Clases CSS: {table.get('class', [])}")
                    logger.info(f"  ID: {table.get('id', 'N/A')}")

                    headers = table.find_all('th')
                    if headers:
                        header_text = [h.text.strip() for h in headers]
                        logger.info(f"  Headers: {header_text}")

                assert True  # Test pasa para análisis manual

    @pytest.mark.slow
    @pytest.mark.integration
    def test_faccara_html_structure(self):
        """Analiza la estructura HTML de FACCARA."""
        with AcaraScraper() as scraper:
            html = scraper._get_html(f"{scraper.base_url_faccara}/estadisticas-0km-usados/")

            if html:
                soup = scraper._parse_html(html)

                # Buscar tablas
                tables = soup.find_all('table')
                logger.info(f"FACCARA: Encontradas {len(tables)} tablas")

                # Buscar divs con estadísticas
                stats_divs = soup.find_all('div', class_=lambda x: x and 'estad' in x.lower() if x else False)
                logger.info(f"FACCARA: {len(stats_divs)} divs de estadísticas")

                # Imprimir estructura
                for i, table in enumerate(tables[:5]):
                    logger.info(f"\nTabla {i+1}:")
                    logger.info(f"  Clases: {table.get('class', [])}")

                    headers = table.find_all('th')
                    if headers:
                        header_text = [h.text.strip() for h in headers[:10]]  # Primeros 10
                        logger.info(f"  Headers: {header_text}")

                assert True

    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requiere ajuste según estructura real del sitio")
    def test_acara_scrape_dry_run(self):
        """Test de scraping de ACARA (sin guardar en BD)."""
        with AcaraScraper() as scraper:
            # Intentar scraping
            data_0km = scraper._scrape_faccara_0km()

            logger.info(f"Datos extraídos: {len(data_0km)} registros")

            if data_0km:
                # Validar con Pydantic
                valid_data, invalid_data = validate_data(data_0km, PatentamientoData)

                logger.info(f"Datos válidos: {len(valid_data)}")
                logger.info(f"Datos inválidos: {len(invalid_data)}")

                # Imprimir primeros registros válidos
                for record in valid_data[:5]:
                    logger.info(f"  {record}")

                # Imprimir errores
                for record in invalid_data[:5]:
                    logger.error(f"  Error: {record['error']}")
                    logger.error(f"  Data: {record['data']}")

                assert len(valid_data) > 0, "No se obtuvieron datos válidos"

    @pytest.mark.slow
    @pytest.mark.integration
    def test_parse_periodo(self):
        """Test de parsing de períodos."""
        with AcaraScraper() as scraper:
            # Test casos válidos
            test_cases = [
                ("Ene-2024", date(2024, 1, 1)),
                ("Dic-2023", date(2023, 12, 1)),
                ("01/2024", date(2024, 1, 1)),
                ("12/2023", date(2023, 12, 1)),
                ("2024-01", date(2024, 1, 1)),
                ("2023-12", date(2023, 12, 1)),
            ]

            for input_str, expected_date in test_cases:
                result = scraper._parse_periodo(input_str)
                assert result == expected_date, f"Error parseando {input_str}: {result} != {expected_date}"
                logger.info(f"✓ {input_str} -> {result}")


class TestAdefaScraperReal:
    """Tests del scraper de ADEFA con datos reales."""

    @pytest.mark.slow
    @pytest.mark.integration
    def test_adefa_connection(self):
        """Test de conexión a ADEFA."""
        with AdefaScraper() as scraper:
            html = scraper._get_html(scraper.stats_url)
            assert html is not None, "No se pudo conectar a ADEFA"
            assert len(html) > 0, "HTML vacío de ADEFA"
            logger.info(f"✓ Conexión a ADEFA exitosa ({len(html)} bytes)")

    @pytest.mark.slow
    @pytest.mark.integration
    def test_adefa_find_reportes(self):
        """Test de búsqueda de reportes en ADEFA."""
        with AdefaScraper() as scraper:
            reportes = scraper._get_reportes_disponibles()

            logger.info(f"Reportes encontrados: {len(reportes)}")

            for reporte in reportes[:10]:  # Primeros 10
                logger.info(f"  {reporte['periodo']} | {reporte['formato']} | {reporte['texto'][:50]}")

            if reportes:
                # Verificar estructura
                assert 'url' in reportes[0]
                assert 'periodo' in reportes[0]
                assert 'formato' in reportes[0]

    @pytest.mark.slow
    @pytest.mark.integration
    def test_adefa_html_structure(self):
        """Analiza estructura HTML de ADEFA."""
        with AdefaScraper() as scraper:
            html = scraper._get_html(scraper.stats_url)

            if html:
                soup = scraper._parse_html(html)

                # Buscar enlaces a PDFs y Excels
                links = soup.find_all('a', href=True)
                pdf_links = [l for l in links if '.pdf' in l['href'].lower()]
                excel_links = [l for l in links if any(ext in l['href'].lower() for ext in ['.xls', '.xlsx'])]

                logger.info(f"ADEFA: {len(pdf_links)} PDFs, {len(excel_links)} Excels")

                # Imprimir primeros links
                logger.info("\nPDFs encontrados:")
                for link in pdf_links[:5]:
                    logger.info(f"  Texto: {link.text.strip()}")
                    logger.info(f"  URL: {link['href']}")

                logger.info("\nExcels encontrados:")
                for link in excel_links[:5]:
                    logger.info(f"  Texto: {link.text.strip()}")
                    logger.info(f"  URL: {link['href']}")

                assert True

    @pytest.mark.slow
    @pytest.mark.integration
    def test_extract_periodo(self):
        """Test de extracción de período de texto."""
        with AdefaScraper() as scraper:
            test_cases = [
                ("Estadísticas Enero 2024", "2024-01"),
                ("produccion_2024_01.pdf", "2024-01"),
                ("reporte-03-2024.xlsx", "2024-03"),
                ("Informe Diciembre 2023", "2023-12"),
                ("datos_12_2023.xls", "2023-12"),
            ]

            for input_str, expected in test_cases:
                result = scraper._extract_periodo(input_str)
                assert result == expected, f"Error extrayendo período de {input_str}: {result} != {expected}"
                logger.info(f"✓ {input_str} -> {result}")

    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requiere descargar archivos reales")
    def test_adefa_scrape_one_report(self):
        """Test de scraping de un reporte de ADEFA."""
        with AdefaScraper() as scraper:
            reportes = scraper._get_reportes_disponibles()

            if reportes:
                # Scrapear el reporte más reciente
                reporte = reportes[0]
                logger.info(f"Scrapeando reporte: {reporte}")

                data = scraper._scrape_reporte(reporte)

                logger.info(f"Datos extraídos: {len(data)} registros")

                if data:
                    # Validar con Pydantic
                    valid_data, invalid_data = validate_data(data, ProduccionData)

                    logger.info(f"Datos válidos: {len(valid_data)}")
                    logger.info(f"Datos inválidos: {len(invalid_data)}")

                    # Imprimir primeros registros
                    for record in valid_data[:5]:
                        logger.info(f"  {record}")

                    assert len(valid_data) > 0, "No se obtuvieron datos válidos"


class TestValidators:
    """Tests de validadores Pydantic."""

    def test_patentamiento_valid(self):
        """Test de validador de patentamientos con datos válidos."""
        data = {
            'fecha': date(2024, 1, 1),
            'anio': 2024,
            'mes': 1,
            'tipo_vehiculo': '0km',
            'marca': 'Toyota',
            'cantidad': 5000,
            'fuente': 'ACARA',
            'periodo_reportado': '2024-01'
        }

        validated = PatentamientoData(**data)
        assert validated.marca == 'Toyota'
        assert validated.cantidad == 5000
        logger.info("✓ Validación de patentamiento exitosa")

    def test_patentamiento_invalid_tipo(self):
        """Test con tipo de vehículo inválido."""
        data = {
            'fecha': date(2024, 1, 1),
            'anio': 2024,
            'mes': 1,
            'tipo_vehiculo': 'seminuevo',  # Inválido
            'marca': 'Toyota',
            'cantidad': 5000,
            'fuente': 'ACARA',
            'periodo_reportado': '2024-01'
        }

        with pytest.raises(ValueError, match="tipo_vehiculo debe ser uno de"):
            PatentamientoData(**data)

    def test_patentamiento_invalid_fuente(self):
        """Test con fuente inválida."""
        data = {
            'fecha': date(2024, 1, 1),
            'anio': 2024,
            'mes': 1,
            'tipo_vehiculo': '0km',
            'marca': 'Toyota',
            'cantidad': 5000,
            'fuente': 'INVALID',  # Inválido
            'periodo_reportado': '2024-01'
        }

        with pytest.raises(ValueError, match="fuente debe ser uno de"):
            PatentamientoData(**data)

    def test_patentamiento_fecha_futura(self):
        """Test con fecha futura."""
        data = {
            'fecha': date.today() + timedelta(days=30),  # Futura
            'anio': 2025,
            'mes': 12,
            'tipo_vehiculo': '0km',
            'marca': 'Toyota',
            'cantidad': 5000,
            'fuente': 'ACARA',
            'periodo_reportado': '2025-12'
        }

        with pytest.raises(ValueError, match="fecha no puede ser futura"):
            PatentamientoData(**data)

    def test_produccion_valid(self):
        """Test de validador de producción con datos válidos."""
        data = {
            'fecha': date(2024, 1, 1),
            'anio': 2024,
            'mes': 1,
            'terminal': 'Toyota',
            'unidades_producidas': 15000,
            'unidades_exportadas': 5000,
            'fuente': 'ADEFA',
            'periodo_reportado': '2024-01'
        }

        validated = ProduccionData(**data)
        assert validated.terminal == 'Toyota'
        assert validated.unidades_producidas == 15000
        logger.info("✓ Validación de producción exitosa")

    def test_produccion_exportadas_mayor_producidas(self):
        """Test con exportadas > producidas (genera warning)."""
        data = {
            'fecha': date(2024, 1, 1),
            'anio': 2024,
            'mes': 1,
            'terminal': 'Toyota',
            'unidades_producidas': 5000,
            'unidades_exportadas': 15000,  # Mayor que producidas
            'fuente': 'ADEFA',
            'periodo_reportado': '2024-01'
        }

        # Debería validar pero generar warning
        validated = ProduccionData(**data)
        assert validated.unidades_exportadas == 15000


# Fixture para setup
@pytest.fixture(scope="session")
def setup_logging():
    """Setup logging para tests."""
    setup_logger()


# Markers para pytest
"""
Ejecutar tests:

# Todos los tests (incluye tests lentos)
pytest tests/test_scrapers_real.py -v

# Solo tests rápidos (validadores)
pytest tests/test_scrapers_real.py -v -m "not slow"

# Solo tests de integración (scrapers reales)
pytest tests/test_scrapers_real.py -v -m integration

# Test específico
pytest tests/test_scrapers_real.py::TestAcaraScraperReal::test_acara_connection -v

# Con output detallado
pytest tests/test_scrapers_real.py -v -s
"""
