"""
Scraper para DNRPA (Dirección Nacional del Registro de la Propiedad Automotor).

Fuente oficial de datos de patentamientos/inscripciones en Argentina.
Obtiene datos con granularidad provincial y por registro seccional.

URL Base: https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/
"""
import time
from typing import Dict, List, Any, Optional
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
from loguru import logger

from backend.config.settings import settings
from backend.models.patentamientos import Patentamiento
from backend.scrapers.validators import PatentamientoData, validate_data
from backend.utils.database import get_db


class DNRPAScraper:
    """
    Scraper para datos oficiales de DNRPA.

    Funcionalidades:
    - Obtener inscripciones (patentamientos) por provincia
    - Obtener inscripciones por registro seccional
    - Datos mensuales por año
    - Separación por tipo de vehículo (Autos, Motos, Maquinarias)
    """

    # Códigos de provincias argentinas
    PROVINCIAS = {
        '01': 'Capital Federal',
        '02': 'Buenos Aires',
        '03': 'Catamarca',
        '04': 'Córdoba',
        '05': 'Corrientes',
        '06': 'Chaco',
        '07': 'Chubut',
        '08': 'Entre Ríos',
        '09': 'Formosa',
        '10': 'Jujuy',
        '11': 'La Pampa',
        '12': 'La Rioja',
        '13': 'Mendoza',
        '14': 'Misiones',
        '15': 'Neuquén',
        '16': 'Río Negro',
        '17': 'Salta',
        '18': 'San Juan',
        '19': 'San Luis',
        '20': 'Santa Cruz',
        '21': 'Santa Fe',
        '22': 'Santiago del Estero',
        '23': 'Tucumán',
        '24': 'Tierra del Fuego',
    }

    # Tipos de vehículos
    TIPOS_VEHICULO = {
        'A': 'Autos',
        'M': 'Motos',
        'Q': 'Maquinarias',  # Asumido, verificar
    }

    # Meses del año
    MESES = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    def __init__(self):
        """Inicializar scraper DNRPA."""
        self.base_url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.scraping_user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9',
            'Referer': 'https://www.dnrpa.gov.ar/'
        })
        self.timeout = settings.scraping_timeout
        self.delay_between_requests = 2  # Segundos entre requests
        # Deshabilitar verificación SSL para desarrollo en Windows
        self.session.verify = False
        # Suprimir warnings de SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        logger.info("[DNRPA] Scraper inicializado")

    def get_provincias_summary(
        self,
        anio: int,
        codigo_tipo: str = 'A',
        codigo_tramite: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Obtiene resumen de inscripciones por provincia (tabla provincial).

        Args:
            anio: Año a consultar
            codigo_tipo: 'A' (Autos), 'M' (Motos), 'Q' (Maquinarias)
            codigo_tramite: 3 (Inscripciones)

        Returns:
            DataFrame con columnas: provincia, mes_1, mes_2, ..., mes_12, total
        """
        url = f"{self.base_url}/tram_prov.php"

        # Usar POST como el navegador (capturado con DevTools)
        data = {
            'anio': str(anio),
            'codigo_tipo': codigo_tipo,
            'operacion': '1',  # ¡PARÁMETRO CRÍTICO!
            'origen': 'portal_dnrpa',
            'tipo_consulta': 'inscripciones',
            'boton': 'Aceptar'
        }

        # Headers adicionales para simular navegador
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.dnrpa.gov.ar',
            'Referer': 'https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php?origen=portal_dnrpa&tipo_consulta=inscripciones',
        }

        try:
            logger.info(f"[DNRPA] Obteniendo resumen provincial {anio} - {self.TIPOS_VEHICULO.get(codigo_tipo, codigo_tipo)}")

            # POST request como el navegador
            response = self.session.post(url, data=data, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Buscar tabla con datos (la que tiene enlaces de provincias)
            tables = soup.find_all('table')
            table = None

            for t in tables:
                # La tabla correcta tiene enlaces con 'tram_prov_'
                if t.find('a', href=lambda x: x and 'tram_prov_' in x):
                    table = t
                    break

            if not table:
                # Fallback: usar la tabla más grande
                table = max(tables, key=lambda t: len(t.find_all('tr'))) if tables else None

            if not table:
                logger.warning("[DNRPA] No se encontró tabla en la página")
                return None

            # Parsear tabla a DataFrame
            df = self._parse_html_table(table)

            if df is not None:
                logger.success(f"[DNRPA] ✓ Obtenidos datos de {len(df)} provincias")

            time.sleep(self.delay_between_requests)

            return df

        except Exception as e:
            logger.error(f"[DNRPA] Error obteniendo resumen provincial: {e}")
            return None

    def get_provincia_detalle(
        self,
        codigo_provincia: str,
        anio: int,
        codigo_tipo: str = 'A',
        codigo_tramite: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Obtiene detalle de inscripciones por registro seccional de una provincia.

        Args:
            codigo_provincia: Código de provincia ('01', '02', etc.)
            anio: Año a consultar
            codigo_tipo: 'A' (Autos), 'M' (Motos), 'Q' (Maquinarias)
            codigo_tramite: 3 (Inscripciones)

        Returns:
            DataFrame con columnas: registro_seccional, mes_1, ..., mes_12, total
        """
        # Construir URL específica de provincia
        # Formato: tram_prov_01.php para provincia '01'
        url = f"{self.base_url}/tram_prov_{codigo_provincia}.php"

        params = {
            'c_provincia': codigo_provincia,
            'codigo_tipo': codigo_tipo,
            'anio': anio,
            'codigo_tramite': codigo_tramite,
            'provincia': codigo_provincia,
            'origen': 'portal_dnrpa'
        }

        try:
            nombre_provincia = self.PROVINCIAS.get(codigo_provincia, f"Provincia {codigo_provincia}")
            tipo_vehiculo = self.TIPOS_VEHICULO.get(codigo_tipo, codigo_tipo)

            logger.info(f"[DNRPA] Obteniendo detalle {nombre_provincia} {anio} - {tipo_vehiculo}")

            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Buscar tabla principal
            table = soup.find('table')

            if not table:
                logger.warning(f"[DNRPA] No se encontró tabla para {nombre_provincia}")
                return None

            # Parsear tabla
            df = self._parse_html_table(table)

            if df is not None:
                # Agregar metadatos
                df['provincia_codigo'] = codigo_provincia
                df['provincia_nombre'] = nombre_provincia
                df['anio'] = anio
                df['tipo_vehiculo_codigo'] = codigo_tipo
                df['tipo_vehiculo'] = tipo_vehiculo

                logger.success(f"[DNRPA] ✓ Obtenidos datos de {len(df)} registros seccionales")

            time.sleep(self.delay_between_requests)

            return df

        except Exception as e:
            logger.error(f"[DNRPA] Error obteniendo detalle provincia {codigo_provincia}: {e}")
            return None

    def _parse_html_table(self, table) -> Optional[pd.DataFrame]:
        """
        Parsea una tabla HTML a DataFrame.

        Args:
            table: Elemento BeautifulSoup de tabla

        Returns:
            DataFrame parseado
        """
        try:
            # Extraer headers
            headers = []
            header_row = table.find('thead') or table.find('tr')

            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))

            # Extraer rows
            rows = []
            tbody = table.find('tbody') or table

            for tr in tbody.find_all('tr')[1:]:  # Saltar header row
                cells = []
                for td in tr.find_all('td'):
                    # Limpiar texto y convertir a número si es posible
                    text = td.get_text(strip=True)
                    # Remover separadores de miles y convertir
                    text_clean = text.replace('.', '').replace(',', '.')

                    try:
                        # Intentar convertir a número
                        value = float(text_clean) if text_clean else 0
                        # Convertir a int si es entero, sino dejar como float
                        if isinstance(value, float) and value == int(value):
                            cells.append(int(value))
                        else:
                            cells.append(value)
                    except ValueError:
                        # Si no es número, dejar como texto
                        cells.append(text)

                if cells:
                    rows.append(cells)

            if not rows:
                return None

            # Crear DataFrame
            if headers and len(headers) == len(rows[0]):
                df = pd.DataFrame(rows, columns=headers)
            else:
                df = pd.DataFrame(rows)

            return df

        except Exception as e:
            logger.error(f"[DNRPA] Error parseando tabla HTML: {e}")
            return None

    def scrape_all_provincias(
        self,
        anio: int,
        codigo_tipo: str = 'A',
        incluir_detalle: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape completo de todas las provincias para un año y tipo de vehículo.

        Args:
            anio: Año a consultar
            codigo_tipo: 'A', 'M', 'Q'
            incluir_detalle: Si True, obtiene detalle por registro seccional

        Returns:
            Dict con resultados del scraping
        """
        logger.info(f"[DNRPA] Iniciando scrape completo {anio} - {self.TIPOS_VEHICULO.get(codigo_tipo)}")

        resultados = {
            'anio': anio,
            'tipo_vehiculo': self.TIPOS_VEHICULO.get(codigo_tipo),
            'resumen_provincial': None,
            'detalles': {},
            'errores': []
        }

        # 1. Obtener resumen provincial
        df_resumen = self.get_provincias_summary(anio, codigo_tipo)

        if df_resumen is not None:
            resultados['resumen_provincial'] = df_resumen

        # 2. Obtener detalle de cada provincia (opcional)
        if incluir_detalle:
            for codigo_prov, nombre_prov in self.PROVINCIAS.items():
                try:
                    df_detalle = self.get_provincia_detalle(codigo_prov, anio, codigo_tipo)

                    if df_detalle is not None:
                        resultados['detalles'][codigo_prov] = df_detalle
                    else:
                        resultados['errores'].append(f"Sin datos para {nombre_prov}")

                except Exception as e:
                    error_msg = f"Error en {nombre_prov}: {str(e)}"
                    logger.warning(f"[DNRPA] {error_msg}")
                    resultados['errores'].append(error_msg)

        logger.success(f"[DNRPA] ✓ Scrape completo finalizado: {len(resultados['detalles'])} provincias")

        return resultados

    def save_to_database(self, df: pd.DataFrame, tipo_vehiculo: str = '0km') -> int:
        """
        Guarda datos de patentamientos en la base de datos.

        Args:
            df: DataFrame con datos
            tipo_vehiculo: Tipo de vehículo ('0km', 'usado')

        Returns:
            Cantidad de registros guardados
        """
        if df is None or df.empty:
            logger.warning("[DNRPA] DataFrame vacío, nada para guardar")
            return 0

        # Convertir DataFrame a formato de patentamientos
        # Esto requiere transformar la tabla de doble entrada (provincia x mes)
        # a registros individuales por fecha

        registros = []

        # Identificar columnas de meses (asumiendo formato 'Enero', 'Febrero', etc.)
        meses_cols = [col for col in df.columns if col in self.MESES.values()]

        for _, row in df.iterrows():
            # Extraer información de la fila
            if 'provincia_nombre' in row:
                provincia = row['provincia_nombre']
            elif 'registro_seccional' in row:
                provincia = row['registro_seccional']
            else:
                provincia = str(row[0])

            # Procesar cada mes
            for mes_nombre in meses_cols:
                cantidad = row[mes_nombre]

                if pd.isna(cantidad) or cantidad == 0:
                    continue

                # Obtener número de mes
                mes_num = [k for k, v in self.MESES.items() if v == mes_nombre][0]

                # Obtener año
                anio = row.get('anio', datetime.now().year)

                # Crear fecha
                fecha = date(int(anio), mes_num, 1)

                registro = {
                    'fecha': fecha,
                    'anio': int(anio),
                    'mes': mes_num,
                    'tipo_vehiculo': tipo_vehiculo,
                    'marca': 'TOTAL',  # DNRPA no desglosa por marca
                    'cantidad': int(cantidad),
                    'provincia': provincia,
                    'fuente': 'DNRPA',
                    'periodo_reportado': f"{anio}-{mes_num:02d}"
                }

                registros.append(registro)

        if not registros:
            logger.warning("[DNRPA] No se generaron registros para guardar")
            return 0

        # Validar con Pydantic
        valid_data, invalid_data = validate_data(registros, PatentamientoData)

        if invalid_data:
            logger.warning(f"[DNRPA] {len(invalid_data)} registros inválidos descartados")

        # Guardar en BD
        saved_count = 0

        with get_db() as db:
            for data in valid_data:
                try:
                    # Verificar si ya existe
                    existing = db.query(Patentamiento).filter(
                        Patentamiento.fecha == data['fecha'],
                        Patentamiento.marca == data['marca'],
                        Patentamiento.tipo_vehiculo == data['tipo_vehiculo'],
                        Patentamiento.provincia == data.get('provincia')
                    ).first()

                    if not existing:
                        patentamiento = Patentamiento(**data)
                        db.add(patentamiento)
                        saved_count += 1
                    else:
                        # Actualizar si cantidad cambió
                        if existing.cantidad != data['cantidad']:
                            existing.cantidad = data['cantidad']
                            existing.updated_at = datetime.utcnow()

                except Exception as e:
                    logger.warning(f"[DNRPA] Error guardando registro: {e}")
                    continue

            db.commit()

        logger.success(f"[DNRPA] ✓ {saved_count} registros guardados en BD")

        return saved_count


# Función standalone para ejecutar el scraper
def scrape_dnrpa(
    anio: int = None,
    tipo_vehiculo: str = 'A',
    guardar_bd: bool = True
) -> Dict[str, Any]:
    """
    Ejecuta el scraper de DNRPA.

    Args:
        anio: Año a consultar (default: año actual)
        tipo_vehiculo: 'A' (Autos), 'M' (Motos), 'Q' (Maquinarias)
        guardar_bd: Si True, guarda en base de datos

    Returns:
        Dict con resultados del scraping
    """
    if anio is None:
        anio = datetime.now().year

    scraper = DNRPAScraper()

    # Scrape completo
    resultados = scraper.scrape_all_provincias(anio, tipo_vehiculo)

    # Guardar en BD si se solicita
    if guardar_bd:
        total_guardados = 0

        # Guardar resumen provincial
        if resultados['resumen_provincial'] is not None:
            guardados = scraper.save_to_database(
                resultados['resumen_provincial'],
                tipo_vehiculo='0km'  # Asumir 0km para autos
            )
            total_guardados += guardados

        # Guardar detalles
        for codigo_prov, df_detalle in resultados['detalles'].items():
            guardados = scraper.save_to_database(df_detalle, tipo_vehiculo='0km')
            total_guardados += guardados

        resultados['total_guardados_bd'] = total_guardados

    return resultados


if __name__ == "__main__":
    from backend.config.logger import setup_logger

    setup_logger()

    # Test: Scrape año actual, autos
    logger.info("=== Test DNRPA Scraper ===")

    # Probar con 2024
    resultados = scrape_dnrpa(anio=2024, tipo_vehiculo='A', guardar_bd=False)

    logger.info(f"Resumen provincial: {resultados['resumen_provincial'] is not None}")
    logger.info(f"Provincias con detalle: {len(resultados['detalles'])}")
    logger.info(f"Errores: {len(resultados['errores'])}")

    if resultados['errores']:
        logger.warning(f"Errores encontrados: {resultados['errores'][:5]}")
