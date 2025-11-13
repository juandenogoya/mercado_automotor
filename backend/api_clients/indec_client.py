"""
Cliente para API del INDEC (Instituto Nacional de Estadística y Censos).

API Documentation:
- Base URL: https://apis.datos.gob.ar/series/api
- IPC: Series temporales
- Endpoint: /series/?ids={serie_id}&start_date={fecha}&limit=5000
"""
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from dateutil.relativedelta import relativedelta
import requests
from loguru import logger

from backend.config.settings import settings
from backend.models.ipc import IPC
from backend.utils.database import get_db


class INDECClient:
    """
    Cliente para interactuar con la API del INDEC.

    Series relevantes para el proyecto:
    - IPC Nivel General: 148.3_INIVELNAL_DICI_M_26
    - IPC Variación Mensual: 148.3_INIVELNALNAL_DICI_M_32
    - IPC Variación Interanual: 148.3_INIVELNALNAL_DICI_M_31
    """

    # IDs de series IPC
    SERIES_IPC = {
        'nivel_general': '148.3_INIVELNAL_DICI_M_26',
        'variacion_mensual': '148.3_INIVELNALNAL_DICI_M_32',
        'variacion_interanual': '148.3_INIVELNALNAL_DICI_M_31',
    }

    def __init__(self):
        self.base_url = "https://apis.datos.gob.ar/series/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
        })
        self.timeout = 30

    def get_ipc_serie(
        self,
        serie_id: str,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        limit: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Obtiene una serie temporal del IPC.

        Args:
            serie_id: ID de la serie
            fecha_desde: Fecha inicial (formato YYYY-MM-DD)
            fecha_hasta: Fecha final (formato YYYY-MM-DD)
            limit: Límite de registros (default: 5000)

        Returns:
            Lista de valores de la serie
        """
        params = {
            'ids': serie_id,
            'limit': limit,
            'format': 'json'
        }

        if fecha_desde:
            params['start_date'] = fecha_desde.strftime('%Y-%m-%d')

        if fecha_hasta:
            params['end_date'] = fecha_hasta.strftime('%Y-%m-%d')

        url = f"{self.base_url}/series"

        logger.info(f"[INDEC] Obteniendo serie {serie_id}...")

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if 'data' not in data:
                logger.warning(f"[INDEC] No se encontraron datos para serie {serie_id}")
                return []

            # Extraer los datos de la serie
            serie_data = data['data']

            logger.success(f"[INDEC] ✓ Obtenidos {len(serie_data)} datos de serie {serie_id}")

            return serie_data

        except requests.RequestException as e:
            logger.error(f"[INDEC] Error obteniendo serie {serie_id}: {e}")
            return []

    def sync_ipc(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Sincroniza datos de IPC desde INDEC a la base de datos.

        Args:
            fecha_desde: Fecha inicial (default: 5 años atrás)
            fecha_hasta: Fecha final (default: hoy)

        Returns:
            Dict con resumen de la sincronización
        """
        if not fecha_hasta:
            fecha_hasta = date.today()

        if not fecha_desde:
            # Por defecto, traer últimos 5 años
            fecha_desde = fecha_hasta - relativedelta(years=5)

        logger.info(f"[INDEC] Sincronizando IPC desde {fecha_desde} hasta {fecha_hasta}...")

        # Obtener todas las series IPC
        series_data = {}
        for nombre, serie_id in self.SERIES_IPC.items():
            try:
                data = self.get_ipc_serie(serie_id, fecha_desde, fecha_hasta)
                series_data[nombre] = data
                logger.info(f"[INDEC] ✓ Serie {nombre}: {len(data)} registros obtenidos")
            except Exception as e:
                logger.error(f"[INDEC] Error obteniendo serie {nombre}: {e}")
                series_data[nombre] = []

        # Combinar las series por fecha
        combined_data = self._combine_series(series_data)

        # Guardar en BD
        saved_count = self._save_ipc_to_db(combined_data)

        result = {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "records_saved": saved_count,
            "date_range": {
                "from": fecha_desde,
                "to": fecha_hasta
            }
        }

        logger.success(f"[INDEC] ✓ Sincronización IPC completada: {saved_count} registros guardados")

        return result

    def _combine_series(self, series_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """
        Combina las series IPC por fecha.

        Args:
            series_data: Dict con {nombre_serie: [datos]}

        Returns:
            Lista de registros combinados por fecha
        """
        # Crear diccionario indexado por fecha
        combined = {}

        # Procesar serie de nivel general (base)
        nivel_general = series_data.get('nivel_general', [])
        for item in nivel_general:
            fecha_str = item[0]  # Primer elemento es la fecha
            valor = item[1]  # Segundo elemento es el valor

            if valor is not None:
                combined[fecha_str] = {
                    'fecha': fecha_str,
                    'nivel_general': float(valor),
                    'variacion_mensual': None,
                    'variacion_interanual': None,
                    'variacion_acumulada': None
                }

        # Agregar variación mensual
        variacion_mensual = series_data.get('variacion_mensual', [])
        for item in variacion_mensual:
            fecha_str = item[0]
            valor = item[1]

            if fecha_str in combined and valor is not None:
                combined[fecha_str]['variacion_mensual'] = float(valor)

        # Agregar variación interanual
        variacion_interanual = series_data.get('variacion_interanual', [])
        for item in variacion_interanual:
            fecha_str = item[0]
            valor = item[1]

            if fecha_str in combined and valor is not None:
                combined[fecha_str]['variacion_interanual'] = float(valor)

        # Convertir a lista ordenada por fecha
        result = sorted(combined.values(), key=lambda x: x['fecha'])

        logger.info(f"[INDEC] ✓ Combinadas {len(result)} fechas únicas")

        return result

    def _save_ipc_to_db(self, data: List[Dict[str, Any]]) -> int:
        """
        Guarda datos de IPC en la base de datos.

        Args:
            data: Lista de registros IPC

        Returns:
            Número de registros guardados
        """
        if not data:
            return 0

        saved_count = 0

        with get_db() as db:
            for record in data:
                try:
                    # Parsear fecha (formato: YYYY-MM-DD)
                    fecha_str = record['fecha']
                    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()

                    # Extraer año y mes
                    anio = fecha_obj.year
                    mes = fecha_obj.month
                    periodo = f"{anio}-{mes:02d}"

                    # Verificar si existe
                    existing = db.query(IPC).filter(
                        IPC.fecha == fecha_obj
                    ).first()

                    if not existing:
                        ipc = IPC(
                            fecha=fecha_obj,
                            anio=anio,
                            mes=mes,
                            nivel_general=record['nivel_general'],
                            variacion_mensual=record.get('variacion_mensual'),
                            variacion_interanual=record.get('variacion_interanual'),
                            variacion_acumulada=record.get('variacion_acumulada'),
                            fuente='INDEC',
                            periodo_reportado=periodo
                        )
                        db.add(ipc)
                        saved_count += 1
                    else:
                        # Actualizar si cambió algún valor
                        updated = False

                        if float(existing.nivel_general) != record['nivel_general']:
                            existing.nivel_general = record['nivel_general']
                            updated = True

                        if record.get('variacion_mensual') and existing.variacion_mensual != record['variacion_mensual']:
                            existing.variacion_mensual = record['variacion_mensual']
                            updated = True

                        if record.get('variacion_interanual') and existing.variacion_interanual != record['variacion_interanual']:
                            existing.variacion_interanual = record['variacion_interanual']
                            updated = True

                        if updated:
                            existing.updated_at = datetime.utcnow()

                except Exception as e:
                    logger.warning(f"[INDEC] Error guardando registro IPC: {e}")
                    continue

            db.commit()

        return saved_count


# Ejemplo de uso
if __name__ == "__main__":
    from backend.config.logger import setup_logger

    setup_logger()

    client = INDECClient()

    # Test: Sincronizar últimos 2 años de IPC
    from dateutil.relativedelta import relativedelta
    fecha_hasta = date.today()
    fecha_desde = fecha_hasta - relativedelta(years=2)

    result = client.sync_ipc(fecha_desde, fecha_hasta)
    print("Resultado:", result)
