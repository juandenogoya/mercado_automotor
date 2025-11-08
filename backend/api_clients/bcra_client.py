"""
Cliente para API del BCRA (Banco Central de la República Argentina).

API Documentation:
- Base URL: https://api.bcra.gob.ar
- Estadísticas: /estadisticas/v2.0
- Cambiarias: /estadisticascambiarias/v1.0
- Créditos Prendarios: /pdfs/BCRAyVos/PRENDARIOS.CSV
"""
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import requests
import pandas as pd
from io import StringIO
from loguru import logger

from backend.config.settings import settings
from backend.models.bcra_indicadores import BCRAIndicador
from backend.utils.database import get_db


class BCRAClient:
    """
    Cliente para interactuar con la API del BCRA.

    Endpoints principales:
    - /estadisticas/v2.0/principales: Principales variables
    - /estadisticas/v2.0/datosvariable/{id_variable}/{desde}/{hasta}: Serie histórica
    - /estadisticascambiarias/v1.0/cotizaciones: Cotizaciones
    """

    # IDs de variables relevantes para el sector automotor
    VARIABLES = {
        'tasa_badlar': 7,  # Tasa BADLAR privada en pesos
        'tasa_pf_30_dias': 8,  # Tasa de plazo fijo a 30 días
        'tasa_pf_90_dias': 9,  # Tasa de plazo fijo a 90 días
        'tipo_cambio_bna': 1,  # Tipo de cambio BNA
        'reservas': 2,  # Reservas internacionales
        'creditos_totales': 16,  # Créditos totales al sector privado
    }

    def __init__(self):
        self.base_url = settings.bcra_api_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
        })
        self.timeout = settings.bcra_timeout
        # Deshabilitar verificación SSL para desarrollo en Windows
        self.session.verify = False
        # Suprimir warnings de SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get_principales_variables(self) -> Dict[str, Any]:
        """
        Obtiene las principales variables económicas del BCRA.

        Returns:
            Dict con las variables y sus valores
        """
        url = f"{self.base_url}/estadisticas/v2.0/principales"

        logger.info(f"[BCRA] Obteniendo principales variables...")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            logger.success(f"[BCRA] ✓ Obtenidas {len(data['results'])} variables")

            return {
                "status": "success",
                "timestamp": datetime.utcnow(),
                "data": data['results']
            }

        except requests.RequestException as e:
            logger.error(f"[BCRA] Error obteniendo principales variables: {e}")
            return {
                "status": "error",
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }

    def get_variable_historica(
        self,
        id_variable: int,
        fecha_desde: date,
        fecha_hasta: date
    ) -> List[Dict[str, Any]]:
        """
        Obtiene serie histórica de una variable.

        Args:
            id_variable: ID de la variable (ver VARIABLES)
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final

        Returns:
            Lista de valores históricos
        """
        # Formato de fecha: YYYY-MM-DD
        desde_str = fecha_desde.strftime('%Y-%m-%d')
        hasta_str = fecha_hasta.strftime('%Y-%m-%d')

        url = f"{self.base_url}/estadisticas/v2.0/datosvariable/{id_variable}/{desde_str}/{hasta_str}"

        logger.info(f"[BCRA] Obteniendo variable {id_variable} desde {desde_str} hasta {hasta_str}...")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            logger.success(f"[BCRA] ✓ Obtenidos {len(data['results'])} datos de variable {id_variable}")

            return data['results']

        except requests.RequestException as e:
            logger.error(f"[BCRA] Error obteniendo variable {id_variable}: {e}")
            return []

    def get_creditos_prendarios(self) -> pd.DataFrame:
        """
        Obtiene datos de créditos prendarios (relevante para automotor).

        Fuente: https://www.bcra.gob.ar/pdfs/BCRAyVos/PRENDARIOS.CSV

        Returns:
            DataFrame con datos de créditos prendarios
        """
        url = "https://www.bcra.gob.ar/pdfs/BCRAyVos/PRENDARIOS.CSV"

        logger.info(f"[BCRA] Obteniendo créditos prendarios...")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # El CSV viene con encoding latin1
            content = response.content.decode('latin1')

            # Parsear CSV
            df = pd.read_csv(
                StringIO(content),
                sep=';',
                decimal=',',
                thousands='.'
            )

            logger.success(f"[BCRA] ✓ Obtenidos {len(df)} registros de créditos prendarios")

            return df

        except Exception as e:
            logger.error(f"[BCRA] Error obteniendo créditos prendarios: {e}")
            return pd.DataFrame()

    def get_cotizaciones(self, fecha: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Obtiene cotizaciones de monedas.

        Args:
            fecha: Fecha específica (None = última disponible)

        Returns:
            Lista de cotizaciones
        """
        if fecha:
            fecha_str = fecha.strftime('%Y-%m-%d')
            url = f"{self.base_url}/estadisticascambiarias/v1.0/cotizaciones/{fecha_str}"
        else:
            url = f"{self.base_url}/estadisticascambiarias/v1.0/cotizaciones"

        logger.info(f"[BCRA] Obteniendo cotizaciones...")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            logger.success(f"[BCRA] ✓ Obtenidas {len(data['results'])} cotizaciones")

            return data['results']

        except requests.RequestException as e:
            logger.error(f"[BCRA] Error obteniendo cotizaciones: {e}")
            return []

    def sync_all_indicators(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Sincroniza todos los indicadores relevantes del BCRA a la base de datos.

        Args:
            fecha_desde: Fecha inicial (default: 30 días atrás)
            fecha_hasta: Fecha final (default: hoy)

        Returns:
            Dict con resumen de la sincronización
        """
        from dateutil.relativedelta import relativedelta

        if not fecha_hasta:
            fecha_hasta = date.today()

        if not fecha_desde:
            fecha_desde = fecha_hasta - relativedelta(months=1)

        logger.info(f"[BCRA] Sincronizando indicadores desde {fecha_desde} hasta {fecha_hasta}...")

        total_saved = 0

        # Sincronizar cada variable
        for var_name, var_id in self.VARIABLES.items():
            try:
                data = self.get_variable_historica(var_id, fecha_desde, fecha_hasta)
                saved = self._save_variable_to_db(var_name, data)
                total_saved += saved

                logger.info(f"[BCRA] ✓ {var_name}: {saved} registros guardados")

            except Exception as e:
                logger.error(f"[BCRA] Error sincronizando {var_name}: {e}")
                continue

        # Sincronizar créditos prendarios
        try:
            df_prendarios = self.get_creditos_prendarios()
            if not df_prendarios.empty:
                saved = self._save_prendarios_to_db(df_prendarios, fecha_desde, fecha_hasta)
                total_saved += saved
                logger.info(f"[BCRA] ✓ Créditos prendarios: {saved} registros guardados")

        except Exception as e:
            logger.error(f"[BCRA] Error sincronizando créditos prendarios: {e}")

        result = {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "records_saved": total_saved,
            "date_range": {
                "from": fecha_desde,
                "to": fecha_hasta
            }
        }

        logger.success(f"[BCRA] ✓ Sincronización completada: {total_saved} registros guardados")

        return result

    def _save_variable_to_db(self, var_name: str, data: List[Dict[str, Any]]) -> int:
        """
        Guarda datos de una variable en la base de datos.
        """
        if not data:
            return 0

        saved_count = 0

        with get_db() as db:
            for record in data:
                try:
                    # Parsear fecha
                    fecha_str = record['fecha']
                    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()

                    # Verificar si existe
                    existing = db.query(BCRAIndicador).filter(
                        BCRAIndicador.fecha == fecha_obj,
                        BCRAIndicador.indicador == var_name
                    ).first()

                    if not existing:
                        indicador = BCRAIndicador(
                            fecha=fecha_obj,
                            indicador=var_name,
                            valor=float(record['valor']),
                            fuente='BCRA',
                            descripcion=record.get('descripcion')
                        )
                        db.add(indicador)
                        saved_count += 1
                    else:
                        # Actualizar si cambió
                        if float(existing.valor) != float(record['valor']):
                            existing.valor = float(record['valor'])
                            existing.updated_at = datetime.utcnow()

                except Exception as e:
                    logger.warning(f"[BCRA] Error guardando registro de {var_name}: {e}")
                    continue

            db.commit()

        return saved_count

    def _save_prendarios_to_db(
        self,
        df: pd.DataFrame,
        fecha_desde: date,
        fecha_hasta: date
    ) -> int:
        """
        Guarda datos de créditos prendarios en la base de datos.
        """
        saved_count = 0

        # Filtrar por rango de fechas
        # Adaptar según estructura real del CSV
        # df_filtered = df[(df['Fecha'] >= fecha_desde) & (df['Fecha'] <= fecha_hasta)]

        with get_db() as db:
            for _, row in df.iterrows():
                try:
                    # Adaptar según estructura real del CSV
                    # Este es un ejemplo genérico

                    # fecha_obj = pd.to_datetime(row['Fecha']).date()
                    # monto = float(row['Monto'])

                    # indicador = BCRAIndicador(
                    #     fecha=fecha_obj,
                    #     indicador='creditos_prendarios',
                    #     valor=monto,
                    #     fuente='BCRA',
                    #     unidad='millones ARS'
                    # )
                    # db.add(indicador)
                    # saved_count += 1

                    pass  # Implementar cuando se analice estructura real

                except Exception as e:
                    logger.warning(f"[BCRA] Error guardando crédito prendario: {e}")
                    continue

            db.commit()

        return saved_count


# Ejemplo de uso
if __name__ == "__main__":
    from backend.config.logger import setup_logger

    setup_logger()

    client = BCRAClient()

    # Test 1: Principales variables
    result = client.get_principales_variables()
    print("Principales variables:", result)

    # Test 2: Sincronizar todo
    from datetime import timedelta
    result = client.sync_all_indicators(
        fecha_desde=date.today() - timedelta(days=30),
        fecha_hasta=date.today()
    )
    print("Sincronización:", result)
