"""
Cliente para API del INDEC (Instituto Nacional de Estadística y Censos).

Fuentes de datos:
- API de Series de Tiempo: https://apis.datos.gob.ar/series/api/
- Excel directo de INDEC: https://www.indec.gob.ar/ftp/cuadros/economia/
- Portal datos.gob.ar: https://datos.gob.ar

Datos disponibles:
- Índices de patentamientos (desde 2014)
- Salarios promedio (sector privado y público)
- IPC - Índice de Precios al Consumidor
- Indicadores económicos varios
"""
from typing import Dict, List, Any, Optional
from datetime import date, datetime, timedelta
import requests
import pandas as pd
from io import BytesIO
from loguru import logger

from backend.config.settings import settings
from backend.models.patentamientos import Patentamiento
from backend.models.bcra_indicadores import BCRAIndicador
from backend.utils.database import get_db


class INDECClient:
    """
    Cliente para API del INDEC y datos abiertos de Argentina.

    Endpoints principales:
    - API Series de Tiempo: https://apis.datos.gob.ar/series/api/
    - Excel patentamientos: https://www.indec.gob.ar/ftp/cuadros/economia/cuadros_indices_patentamientos.xls
    - Portal datos.gob.ar: https://datos.gob.ar

    Funcionalidades:
    - Obtener índices de patentamientos (serie original y desestacionalizada)
    - Obtener salarios promedio
    - Obtener IPC (inflación)
    - Obtener indicadores económicos varios
    """

    # IDs de series en la API de Series de Tiempo
    # Fuente: https://datos.gob.ar/series/api
    # Documentación: https://datosgobar.github.io/series-tiempo-ar-api/
    #
    # IMPORTANTE: Estos IDs fueron obtenidos de la documentación oficial del INDEC
    # y datos.gob.ar. La API es pública y gratuita, pero puede estar sujeta a
    # restricciones de acceso por región/red.
    #
    # Para validar series: usar backend/scripts/explore_indec_series.py
    # Para descubrir nuevas series: https://datos.gob.ar/series/api/search
    #
    # ⚠️  NOTA: Algunos IDs pueden cambiar con el tiempo. Si una serie retorna error 400,
    # verificar el ID correcto en: https://datos.gob.ar/dataset
    SERIES_IDS = {
        # IPC - Índice de Precios al Consumidor (✅ VERIFICADO - FUNCIONA)
        'ipc_nacional': '148.3_INIVELNAL_DICI_M_26',  # IPC Nivel General
        'ipc_alimentos': '148.3_INALIBED_DICI_M_29',  # IPC Alimentos y Bebidas
        'ipc_transporte': '148.3_INTRANSP_DICI_M_33',  # IPC Transporte (relevante para autos)
        'ipc_core': '148.3_INUCLEOD_DICI_M_40',  # IPC Núcleo (sin estacionales)

        # Actividad Económica (✅ VERIFICADO - FUNCIONA)
        'emae': '143.3_NO_PR_2004_A_21',  # EMAE - Estimador Mensual Actividad Económica
        'emae_desest': '143.3_NO_PR_2004_A_28',  # EMAE Desestacionalizada

        # ⚠️  DESHABILITADO TEMPORALMENTE - IDs retornan error 400 (Bad Request)
        # Estos IDs necesitan ser verificados y actualizados en datos.gob.ar
        # Para buscar IDs correctos visitar: https://datos.gob.ar/dataset

        # Salarios (⚠️  REQUIERE VERIFICACIÓN)
        # 'salario_indice': '11.3_ISAC_0_M_18',  # ERROR 400 - ID incorrecto
        # 'salario_privado': '11.3_ISAPRI_0_M_22',
        # 'salario_publico': '11.3_ISAPUB_0_M_24',

        # Producción Industrial (⚠️  REQUIERE VERIFICACIÓN)
        # 'ipi_general': '133.2_OFIEIBOV_DICI_M_19',
        # 'ipi_automotriz': '133.2_OFABAUT_DICI_M_42',  # ERROR 400 - ID incorrecto

        # Comercio (⚠️  REQUIERE VERIFICACIÓN)
        # 'ventas_super': '134.3_IVSMSTO_DICI_M_13',  # ERROR 400 - ID incorrecto
        # 'ventas_shoppings': '134.4_IVSHSTO_DICI_M_17',

        # Construcción (⚠️  REQUIERE VERIFICACIÓN)
        # 'isac': '137.2_ISBISTOD_DICI_M_16',

        # Empleo (⚠️  REQUIERE VERIFICACIÓN)
        # 'empleo_privado': '11.5_ITCRP_0_M_21',  # ERROR 400 - ID incorrecto

        # Patentamientos: se obtiene del Excel directo de INDEC
    }

    def __init__(self):
        """Inicializar cliente INDEC."""
        self.api_base_url = "https://apis.datos.gob.ar/series/api"
        self.indec_ftp_base = "https://www.indec.gob.ar/ftp/cuadros/economia"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.scraping_user_agent,
            'Accept': 'application/json'
        })
        self.timeout = settings.scraping_timeout
        # Deshabilitar verificación SSL para desarrollo en Windows
        self.session.verify = False
        # Suprimir warnings de SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        logger.info("[INDEC] Cliente inicializado")

    def get_series(
        self,
        series_id: str,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        formato: str = 'json'
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de una serie de tiempo de la API.

        Args:
            series_id: ID de la serie (ej: '148.3_INIVELNAL_DICI_M_26')
            fecha_desde: Fecha inicial (default: None = desde inicio)
            fecha_hasta: Fecha final (default: None = hasta hoy)
            formato: Formato de respuesta ('json' o 'csv')

        Returns:
            Dict con datos de la serie o None si falla
        """
        url = f"{self.api_base_url}/series/"

        params = {
            'ids': series_id,
            'format': formato
        }

        if fecha_desde:
            params['start_date'] = fecha_desde.isoformat()

        if fecha_hasta:
            params['end_date'] = fecha_hasta.isoformat()

        try:
            logger.info(f"[INDEC] Consultando serie: {series_id}")

            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            if formato == 'json':
                data = response.json()
                logger.success(f"[INDEC] ✓ Serie {series_id} obtenida")
                return data
            else:
                logger.success(f"[INDEC] ✓ Serie {series_id} obtenida (CSV)")
                return {'data': response.text}

        except Exception as e:
            logger.error(f"[INDEC] Error obteniendo serie {series_id}: {e}")
            return None

    def get_patentamientos_excel(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        serie_tipo: str = 'original'
    ) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Obtiene datos de patentamientos desde el Excel de INDEC.

        El Excel contiene múltiples hojas con:
        - Serie original (índice base 2014=100)
        - Serie desestacionalizada
        - Desagregación por categoría (autos, motos, camiones, etc.)
        - Desagregación por provincia
        - Desagregación por origen (nacional/importado)

        Args:
            fecha_desde: Fecha inicial de filtro
            fecha_hasta: Fecha final de filtro
            serie_tipo: 'original' o 'desestacionalizada' o 'ambas'

        Returns:
            Dict con DataFrames procesados por categoría o None
        """
        url = f"{self.indec_ftp_base}/cuadros_indices_patentamientos.xls"

        try:
            logger.info("[INDEC] Descargando Excel de patentamientos...")

            response = self.session.get(url, timeout=60)
            response.raise_for_status()

            # Leer Excel (puede tener múltiples hojas)
            excel_file = BytesIO(response.content)
            sheets = pd.read_excel(excel_file, sheet_name=None)

            logger.success(f"[INDEC] ✓ Excel descargado: {len(sheets)} hojas")

            # Procesar hojas según estructura típica del INDEC
            processed_data = {}

            for sheet_name, df in sheets.items():
                logger.info(f"[INDEC]   Procesando hoja: {sheet_name}")

                try:
                    # El Excel del INDEC típicamente tiene:
                    # - Fila 0-5: Metadata/títulos
                    # - Fila 6-7: Headers
                    # - Filas siguientes: Datos

                    # Identificar fila de headers (buscar "Período" o fechas)
                    header_row = None
                    for i in range(min(10, len(df))):
                        row_str = ' '.join(str(val) for val in df.iloc[i].values if pd.notna(val))
                        if 'Período' in row_str or 'Periodo' in row_str or any(str(val).startswith('20') for val in df.iloc[i].values if pd.notna(val)):
                            header_row = i
                            break

                    if header_row is not None:
                        # Crear nuevo DataFrame con headers correctos
                        df_clean = df.iloc[header_row+1:].copy()
                        df_clean.columns = df.iloc[header_row].values

                        # Limpiar columnas
                        df_clean = df_clean.dropna(how='all')  # Eliminar filas vacías
                        df_clean = df_clean.reset_index(drop=True)

                        # Intentar parsear columna de fecha/período
                        if 'Período' in df_clean.columns or 'Periodo' in df_clean.columns:
                            periodo_col = 'Período' if 'Período' in df_clean.columns else 'Periodo'

                            # Convertir período a fecha
                            df_clean['fecha'] = pd.to_datetime(
                                df_clean[periodo_col],
                                format='%Y-%m',
                                errors='coerce'
                            )

                            # Aplicar filtros de fecha si se especificaron
                            if fecha_desde:
                                df_clean = df_clean[df_clean['fecha'] >= pd.Timestamp(fecha_desde)]
                            if fecha_hasta:
                                df_clean = df_clean[df_clean['fecha'] <= pd.Timestamp(fecha_hasta)]

                        processed_data[sheet_name] = df_clean
                        logger.info(f"[INDEC]     ✓ {len(df_clean)} registros procesados")

                    else:
                        logger.warning(f"[INDEC]     ⚠ No se encontró header en hoja {sheet_name}")

                except Exception as e:
                    logger.error(f"[INDEC]     Error procesando hoja {sheet_name}: {e}")
                    continue

            if not processed_data:
                logger.error("[INDEC] No se pudo procesar ninguna hoja del Excel")
                return None

            logger.success(f"[INDEC] ✓ Procesadas {len(processed_data)} hojas exitosamente")
            return processed_data

        except Exception as e:
            logger.error(f"[INDEC] Error descargando Excel de patentamientos: {e}")
            return None

    def get_patentamientos(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        serie_tipo: str = 'original'
    ) -> List[Dict[str, Any]]:
        """
        Obtiene índices de patentamientos del INDEC.

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            serie_tipo: 'original' o 'desestacionalizada'

        Returns:
            Lista de diccionarios con datos de patentamientos
        """
        logger.info(f"[INDEC] Obteniendo patentamientos ({serie_tipo})...")

        try:
            # Intentar obtener del Excel
            df = self.get_patentamientos_excel(fecha_desde, fecha_hasta)

            if df is None:
                logger.warning("[INDEC] No se pudo obtener datos de patentamientos")
                return []

            # Parsear DataFrame a lista de registros
            # Nota: Esto requiere conocer la estructura exacta del Excel
            # Este es un placeholder que debe ajustarse según estructura real

            registros = []

            logger.info(f"[INDEC] ✓ Obtenidos {len(registros)} registros de patentamientos")
            return registros

        except Exception as e:
            logger.error(f"[INDEC] Error obteniendo patentamientos: {e}")
            return []

    def get_ipc(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        categoria: str = 'nacional'
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene el Índice de Precios al Consumidor (IPC).

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            categoria: 'nacional', 'alimentos', etc.

        Returns:
            Lista de valores de IPC por fecha
        """
        series_map = {
            'nacional': self.SERIES_IDS['ipc_nacional'],
            'alimentos': self.SERIES_IDS['ipc_alimentos']
        }

        series_id = series_map.get(categoria, self.SERIES_IDS['ipc_nacional'])

        logger.info(f"[INDEC] Obteniendo IPC ({categoria})...")

        data = self.get_series(
            series_id=series_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        if not data:
            return None

        try:
            # Parsear respuesta de la API
            # Formato típico: {'data': [[fecha, valor], ...]}
            series_data = data.get('data', [])

            registros = []
            for punto in series_data:
                if len(punto) >= 2:
                    fecha_str, valor = punto[0], punto[1]

                    # Parsear fecha (formato ISO)
                    try:
                        fecha_obj = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')).date()
                    except:
                        # Fallback: asumir formato YYYY-MM-DD
                        fecha_obj = datetime.strptime(fecha_str[:10], '%Y-%m-%d').date()

                    registros.append({
                        'fecha': fecha_obj,
                        'indicador': f'ipc_{categoria}',
                        'valor': float(valor),
                        'unidad': 'índice',
                        'fuente': 'INDEC'
                    })

            logger.success(f"[INDEC] ✓ Obtenidos {len(registros)} valores de IPC")
            return registros

        except Exception as e:
            logger.error(f"[INDEC] Error parseando IPC: {e}")
            return None

    def get_salario_promedio(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> Optional[float]:
        """
        Obtiene el salario promedio más reciente.

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final

        Returns:
            Salario promedio en ARS o None
        """
        logger.info("[INDEC] Obteniendo salario promedio...")

        # Intentar obtener del índice de salarios
        data = self.get_series(
            series_id=self.SERIES_IDS['salario_indice'],
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        if not data:
            logger.warning("[INDEC] No se pudo obtener índice de salarios")
            return None

        try:
            # Obtener último valor
            series_data = data.get('data', [])

            if not series_data:
                return None

            # Último punto de datos
            ultimo_punto = series_data[-1]
            indice_salario = float(ultimo_punto[1])

            # Nota: El índice de salarios es un número índice (base 100)
            # Para obtener salario promedio en ARS, necesitamos un valor base
            # Este valor debe ajustarse según datos reales

            # Aproximación: Si índice base 2016 = 100, y ese año salario promedio era ~300k
            # Entonces: salario_actual = (indice_actual / 100) * 300000

            # Este es un cálculo simplificado que debe ajustarse con datos reales
            salario_base_2016 = 300_000  # ARS (ejemplo, debe verificarse)
            salario_estimado = (indice_salario / 100) * salario_base_2016

            logger.success(f"[INDEC] ✓ Salario promedio estimado: ${salario_estimado:,.0f}")

            return salario_estimado

        except Exception as e:
            logger.error(f"[INDEC] Error calculando salario promedio: {e}")
            return None

    def get_emae(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        desestacionalizada: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene el Estimador Mensual de Actividad Económica (EMAE).

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            desestacionalizada: True para serie desestacionalizada

        Returns:
            Lista de valores de EMAE por fecha
        """
        series_id = self.SERIES_IDS['emae_desest'] if desestacionalizada else self.SERIES_IDS['emae']
        tipo = 'desestacionalizada' if desestacionalizada else 'original'

        logger.info(f"[INDEC] Obteniendo EMAE ({tipo})...")

        data = self.get_series(
            series_id=series_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        if not data:
            return None

        try:
            series_data = data.get('data', [])
            registros = []

            for punto in series_data:
                if len(punto) >= 2:
                    fecha_str, valor = punto[0], punto[1]

                    try:
                        fecha_obj = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')).date()
                    except:
                        fecha_obj = datetime.strptime(fecha_str[:10], '%Y-%m-%d').date()

                    registros.append({
                        'fecha': fecha_obj,
                        'indicador': f'emae_{tipo}',
                        'valor': float(valor),
                        'unidad': 'índice',
                        'fuente': 'INDEC'
                    })

            logger.success(f"[INDEC] ✓ Obtenidos {len(registros)} valores de EMAE")
            return registros

        except Exception as e:
            logger.error(f"[INDEC] Error parseando EMAE: {e}")
            return None

    def get_ipi(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        sector: str = 'general'
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene el Índice de Producción Industrial (IPI).

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            sector: 'general' o 'automotriz'

        Returns:
            Lista de valores de IPI por fecha
        """
        series_map = {
            'general': self.SERIES_IDS['ipi_general'],
            'automotriz': self.SERIES_IDS['ipi_automotriz']
        }

        series_id = series_map.get(sector, self.SERIES_IDS['ipi_general'])

        logger.info(f"[INDEC] Obteniendo IPI ({sector})...")

        data = self.get_series(
            series_id=series_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        if not data:
            return None

        try:
            series_data = data.get('data', [])
            registros = []

            for punto in series_data:
                if len(punto) >= 2:
                    fecha_str, valor = punto[0], punto[1]

                    try:
                        fecha_obj = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')).date()
                    except:
                        fecha_obj = datetime.strptime(fecha_str[:10], '%Y-%m-%d').date()

                    registros.append({
                        'fecha': fecha_obj,
                        'indicador': f'ipi_{sector}',
                        'valor': float(valor),
                        'unidad': 'índice',
                        'fuente': 'INDEC'
                    })

            logger.success(f"[INDEC] ✓ Obtenidos {len(registros)} valores de IPI")
            return registros

        except Exception as e:
            logger.error(f"[INDEC] Error parseando IPI: {e}")
            return None

    def get_empleo(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene el Índice de Trabajadores Registrados (Empleo Privado).

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final

        Returns:
            Lista de valores de empleo por fecha
        """
        logger.info("[INDEC] Obteniendo datos de empleo...")

        data = self.get_series(
            series_id=self.SERIES_IDS['empleo_privado'],
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        if not data:
            return None

        try:
            series_data = data.get('data', [])
            registros = []

            for punto in series_data:
                if len(punto) >= 2:
                    fecha_str, valor = punto[0], punto[1]

                    try:
                        fecha_obj = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')).date()
                    except:
                        fecha_obj = datetime.strptime(fecha_str[:10], '%Y-%m-%d').date()

                    registros.append({
                        'fecha': fecha_obj,
                        'indicador': 'empleo_privado',
                        'valor': float(valor),
                        'unidad': 'índice',
                        'fuente': 'INDEC'
                    })

            logger.success(f"[INDEC] ✓ Obtenidos {len(registros)} valores de empleo")
            return registros

        except Exception as e:
            logger.error(f"[INDEC] Error parseando empleo: {e}")
            return None

    def get_ventas(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        canal: str = 'supermercados'
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene índices de ventas (supermercados o shoppings).

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            canal: 'supermercados' o 'shoppings'

        Returns:
            Lista de valores de ventas por fecha
        """
        series_map = {
            'supermercados': self.SERIES_IDS['ventas_super'],
            'shoppings': self.SERIES_IDS['ventas_shoppings']
        }

        series_id = series_map.get(canal, self.SERIES_IDS['ventas_super'])

        logger.info(f"[INDEC] Obteniendo ventas ({canal})...")

        data = self.get_series(
            series_id=series_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        if not data:
            return None

        try:
            series_data = data.get('data', [])
            registros = []

            for punto in series_data:
                if len(punto) >= 2:
                    fecha_str, valor = punto[0], punto[1]

                    try:
                        fecha_obj = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')).date()
                    except:
                        fecha_obj = datetime.strptime(fecha_str[:10], '%Y-%m-%d').date()

                    registros.append({
                        'fecha': fecha_obj,
                        'indicador': f'ventas_{canal}',
                        'valor': float(valor),
                        'unidad': 'índice',
                        'fuente': 'INDEC'
                    })

            logger.success(f"[INDEC] ✓ Obtenidos {len(registros)} valores de ventas")
            return registros

        except Exception as e:
            logger.error(f"[INDEC] Error parseando ventas: {e}")
            return None

    def get_construccion(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene el Índice Sintético de la Actividad de la Construcción (ISAC).

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final

        Returns:
            Lista de valores de construcción por fecha
        """
        logger.info("[INDEC] Obteniendo ISAC (construcción)...")

        data = self.get_series(
            series_id=self.SERIES_IDS['isac'],
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        if not data:
            return None

        try:
            series_data = data.get('data', [])
            registros = []

            for punto in series_data:
                if len(punto) >= 2:
                    fecha_str, valor = punto[0], punto[1]

                    try:
                        fecha_obj = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')).date()
                    except:
                        fecha_obj = datetime.strptime(fecha_str[:10], '%Y-%m-%d').date()

                    registros.append({
                        'fecha': fecha_obj,
                        'indicador': 'isac',
                        'valor': float(valor),
                        'unidad': 'índice',
                        'fuente': 'INDEC'
                    })

            logger.success(f"[INDEC] ✓ Obtenidos {len(registros)} valores de construcción")
            return registros

        except Exception as e:
            logger.error(f"[INDEC] Error parseando construcción: {e}")
            return None

    def _sync_generic_indicator(
        self,
        registros: List[Dict[str, Any]],
        indicador_nombre: str
    ) -> Dict[str, Any]:
        """
        Método genérico para sincronizar cualquier indicador con la BD.

        Args:
            registros: Lista de registros a guardar
            indicador_nombre: Nombre del indicador para logging

        Returns:
            Dict con resultado de sincronización
        """
        if not registros:
            return {
                'status': 'error',
                'message': f'No se pudieron obtener datos de {indicador_nombre}'
            }

        saved_count = 0

        with get_db() as db:
            for registro in registros:
                try:
                    # Verificar si ya existe
                    existing = db.query(BCRAIndicador).filter(
                        BCRAIndicador.fecha == registro['fecha'],
                        BCRAIndicador.indicador == registro['indicador']
                    ).first()

                    if not existing:
                        indicador = BCRAIndicador(**registro)
                        db.add(indicador)
                        saved_count += 1
                    else:
                        # Actualizar si cambió
                        if existing.valor != registro['valor']:
                            existing.valor = registro['valor']
                            existing.updated_at = datetime.utcnow()

                except Exception as e:
                    logger.warning(f"[INDEC] Error guardando {indicador_nombre}: {e}")
                    continue

            db.commit()

        logger.success(f"[INDEC] ✓ {indicador_nombre} sincronizado: {saved_count} registros guardados")

        return {
            'status': 'success',
            'records_obtained': len(registros),
            'records_saved': saved_count
        }

    def sync_ipc(
        self,
        fecha_desde: Optional[date] = None,
        meses_atras: int = 12
    ) -> Dict[str, Any]:
        """
        Sincroniza datos de IPC con la base de datos.

        Args:
            fecha_desde: Fecha inicial (default: 12 meses atrás)
            meses_atras: Meses hacia atrás si no se especifica fecha_desde

        Returns:
            Dict con resultado de sincronización
        """
        if not fecha_desde:
            fecha_desde = date.today() - timedelta(days=meses_atras * 30)

        fecha_hasta = date.today()

        logger.info(f"[INDEC] Sincronizando IPC desde {fecha_desde} hasta {fecha_hasta}")

        # Obtener IPC nacional
        registros_ipc = self.get_ipc(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            categoria='nacional'
        )

        if not registros_ipc:
            return {
                'status': 'error',
                'message': 'No se pudieron obtener datos de IPC'
            }

        # Guardar en BD (usar tabla bcra_indicadores que tiene estructura genérica)
        saved_count = 0

        with get_db() as db:
            for registro in registros_ipc:
                try:
                    # Verificar si ya existe
                    existing = db.query(BCRAIndicador).filter(
                        BCRAIndicador.fecha == registro['fecha'],
                        BCRAIndicador.indicador == registro['indicador']
                    ).first()

                    if not existing:
                        indicador = BCRAIndicador(**registro)
                        db.add(indicador)
                        saved_count += 1
                    else:
                        # Actualizar si cambió
                        if existing.valor != registro['valor']:
                            existing.valor = registro['valor']
                            existing.updated_at = datetime.utcnow()

                except Exception as e:
                    logger.warning(f"[INDEC] Error guardando IPC: {e}")
                    continue

            db.commit()

        logger.success(f"[INDEC] ✓ IPC sincronizado: {saved_count} registros guardados")

        return {
            'status': 'success',
            'records_obtained': len(registros_ipc),
            'records_saved': saved_count,
            'date_range': {
                'from': fecha_desde,
                'to': fecha_hasta
            }
        }

    def sync_all_indicators(
        self,
        fecha_desde: Optional[date] = None,
        meses_atras: int = 12
    ) -> Dict[str, Any]:
        """
        Sincroniza todos los indicadores del INDEC.

        Args:
            fecha_desde: Fecha inicial
            meses_atras: Meses hacia atrás si no se especifica fecha_desde

        Returns:
            Dict con resultado de sincronización completa
        """
        logger.info("[INDEC] Iniciando sincronización completa...")

        resultados = {
            'status': 'success',
            'timestamp': datetime.utcnow(),
            'indicadores': {}
        }

        # 1. Sincronizar IPC
        try:
            result_ipc = self.sync_ipc(fecha_desde, meses_atras)
            resultados['indicadores']['ipc'] = result_ipc
        except Exception as e:
            logger.error(f"[INDEC] Error sincronizando IPC: {e}")
            resultados['indicadores']['ipc'] = {'status': 'error', 'error': str(e)}

        # 2. Obtener salario promedio más reciente
        try:
            salario = self.get_salario_promedio()
            resultados['indicadores']['salario_promedio'] = {
                'status': 'success',
                'valor': salario,
                'fecha': date.today()
            }
        except Exception as e:
            logger.error(f"[INDEC] Error obteniendo salario: {e}")
            resultados['indicadores']['salario_promedio'] = {'status': 'error', 'error': str(e)}

        # 3. Sincronizar EMAE (Actividad Económica)
        try:
            if not fecha_desde:
                fecha_desde = date.today() - timedelta(days=meses_atras * 30)
            registros_emae = self.get_emae(fecha_desde=fecha_desde, fecha_hasta=date.today())
            result_emae = self._sync_generic_indicator(registros_emae, 'EMAE')
            resultados['indicadores']['emae'] = result_emae
        except Exception as e:
            logger.error(f"[INDEC] Error sincronizando EMAE: {e}")
            resultados['indicadores']['emae'] = {'status': 'error', 'error': str(e)}

        # ⚠️  TEMPORALMENTE DESHABILITADO - Series comentadas por IDs incorrectos
        # Para habilitar estas series, primero verificar IDs correctos en:
        # https://datos.gob.ar/dataset

        # 4. Sincronizar IPI Automotriz (Producción Industrial) - DESHABILITADO
        logger.warning("[INDEC] ⚠️  IPI Automotriz deshabilitado - ID de serie requiere verificación")
        resultados['indicadores']['ipi_automotriz'] = {
            'status': 'disabled',
            'message': 'ID de serie requiere verificación en datos.gob.ar'
        }
        # try:
        #     registros_ipi = self.get_ipi(fecha_desde=fecha_desde, fecha_hasta=date.today(), sector='automotriz')
        #     result_ipi = self._sync_generic_indicator(registros_ipi, 'IPI Automotriz')
        #     resultados['indicadores']['ipi_automotriz'] = result_ipi
        # except Exception as e:
        #     logger.error(f"[INDEC] Error sincronizando IPI: {e}")
        #     resultados['indicadores']['ipi_automotriz'] = {'status': 'error', 'error': str(e)}

        # 5. Sincronizar Empleo - DESHABILITADO
        logger.warning("[INDEC] ⚠️  Empleo deshabilitado - ID de serie requiere verificación")
        resultados['indicadores']['empleo'] = {
            'status': 'disabled',
            'message': 'ID de serie requiere verificación en datos.gob.ar'
        }
        # try:
        #     registros_empleo = self.get_empleo(fecha_desde=fecha_desde, fecha_hasta=date.today())
        #     result_empleo = self._sync_generic_indicator(registros_empleo, 'Empleo')
        #     resultados['indicadores']['empleo'] = result_empleo
        # except Exception as e:
        #     logger.error(f"[INDEC] Error sincronizando empleo: {e}")
        #     resultados['indicadores']['empleo'] = {'status': 'error', 'error': str(e)}

        # 6. Sincronizar Ventas Supermercados - DESHABILITADO
        logger.warning("[INDEC] ⚠️  Ventas deshabilitado - ID de serie requiere verificación")
        resultados['indicadores']['ventas'] = {
            'status': 'disabled',
            'message': 'ID de serie requiere verificación en datos.gob.ar'
        }
        # try:
        #     registros_ventas = self.get_ventas(fecha_desde=fecha_desde, fecha_hasta=date.today(), canal='supermercados')
        #     result_ventas = self._sync_generic_indicator(registros_ventas, 'Ventas')
        #     resultados['indicadores']['ventas'] = result_ventas
        # except Exception as e:
        #     logger.error(f"[INDEC] Error sincronizando ventas: {e}")
        #     resultados['indicadores']['ventas'] = {'status': 'error', 'error': str(e)}

        # 7. Sincronizar Construcción (ISAC) - DESHABILITADO
        logger.warning("[INDEC] ⚠️  Construcción (ISAC) deshabilitado - ID de serie requiere verificación")
        resultados['indicadores']['construccion'] = {
            'status': 'disabled',
            'message': 'ID de serie requiere verificación en datos.gob.ar'
        }
        # try:
        #     registros_construccion = self.get_construccion(fecha_desde=fecha_desde, fecha_hasta=date.today())
        #     result_construccion = self._sync_generic_indicator(registros_construccion, 'ISAC')
        #     resultados['indicadores']['construccion'] = result_construccion
        # except Exception as e:
        #     logger.error(f"[INDEC] Error sincronizando construcción: {e}")
        #     resultados['indicadores']['construccion'] = {'status': 'error', 'error': str(e)}

        # Patentamientos (opcional, puede ser pesado)
        # Comentado por ahora, activar si es necesario
        # try:
        #     result_pat = self.sync_patentamientos(fecha_desde, meses_atras)
        #     resultados['indicadores']['patentamientos'] = result_pat
        # except Exception as e:
        #     logger.error(f"[INDEC] Error sincronizando patentamientos: {e}")

        logger.success("[INDEC] ✓ Sincronización completa finalizada")

        return resultados


# Ejemplo de uso
if __name__ == "__main__":
    from backend.config.logger import setup_logger

    setup_logger()

    client = INDECClient()

    # Test: Obtener IPC
    print("\n=== Test IPC ===")
    ipc_data = client.get_ipc(
        fecha_desde=date(2024, 1, 1),
        fecha_hasta=date.today()
    )

    if ipc_data:
        print(f"Obtenidos {len(ipc_data)} registros de IPC")
        print(f"Último: {ipc_data[-1]}")

    # Test: Obtener salario promedio
    print("\n=== Test Salario ===")
    salario = client.get_salario_promedio()
    print(f"Salario promedio estimado: ${salario:,.0f}")

    # Test: Sincronización completa
    print("\n=== Test Sincronización ===")
    result = client.sync_all_indicators(meses_atras=3)
    print(result)
