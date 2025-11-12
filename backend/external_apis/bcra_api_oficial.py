#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente para la API oficial v4.0 del BCRA (Banco Central de la República Argentina).

API oficial: https://api.bcra.gob.ar/estadisticas/v4.0
Documentación: https://www.bcra.gob.ar/BCRAyVos/Estadisticas_new.asp

Variables principales:
- Monetarias: Reservas, Tipo de cambio, Base monetaria, BADLAR, LELIQs
- Inflación: IPC mensual, IPC interanual, CER, UVA, UVI

Uso:
    from backend.external_apis.bcra_api_oficial import BCRAClientOficial

    client = BCRAClientOficial()

    # Obtener datos de una variable
    df = client.get_variable_data(variable_id=1, desde='2020-01-01')  # Reservas

    # Obtener múltiples variables
    df_multiple = client.get_multiple_variables(
        variable_ids=[1, 5, 7],  # Reservas, TC, BADLAR
        desde='2020-01-01'
    )
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
import urllib3

# Deshabilitar warnings de SSL (el certificado del BCRA tiene problemas)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BCRAClientOficial:
    """
    Cliente para la API oficial v4.0 del BCRA.
    """

    BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0"

    # Variables monetarias disponibles
    VARIABLES_MONETARIAS = {
        1: "Reservas internacionales",
        5: "Tipo de cambio mayorista (USD/ARS)",
        7: "BADLAR bancos privados",
        9: "Tasa de política monetaria",
        11: "LELIQ",
        15: "Base monetaria",
        16: "Circulación monetaria",
        17: "Billetes en circulación",
        18: "Monedas en circulación",
        19: "Depósitos en cuenta corriente",
        20: "Depósitos en caja de ahorro",
        21: "Depósitos a plazo fijo"
    }

    # Variables de inflación e índices
    VARIABLES_INFLACION = {
        27: "IPC Nivel General - Variación mensual",
        28: "IPC Nivel General - Variación interanual",
        30: "CER (Coeficiente de Estabilización de Referencia)",
        31: "UVA (Unidad de Valor Adquisitivo)",
        32: "UVI (Unidad de Vivienda)",
        40: "ICL (Índice para Contratos de Locación)"
    }

    def __init__(self, verify_ssl: bool = False, timeout: int = 30):
        """
        Inicializa el cliente BCRA oficial.

        Args:
            verify_ssl: Si verificar SSL (False por defecto debido a problemas con certificado BCRA)
            timeout: Timeout para requests (segundos)
        """
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()

    def get_all_variables(self) -> Dict[str, Any]:
        """
        Obtiene lista completa de variables disponibles.

        Returns:
            Dict con la respuesta de la API incluyendo todas las variables
        """
        url = f"{self.BASE_URL}/monetarias"

        try:
            logger.info(f"Solicitando variables desde: {url}")
            response = self.session.get(url, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            count = data.get('metadata', {}).get('resultset', {}).get('count', 0)
            logger.info(f"Variables obtenidas: {count}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener variables: {e}")
            raise

    def get_variable_data(
        self,
        variable_id: int,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Obtiene datos históricos de una variable específica.

        Args:
            variable_id: ID de la variable (ej: 1 para Reservas, 5 para TC)
            desde: Fecha de inicio en formato YYYY-MM-DD (opcional)
            hasta: Fecha de fin en formato YYYY-MM-DD (opcional)
            limit: Máximo de registros a obtener (default: 1000)

        Returns:
            DataFrame con columnas: fecha, valor, variable_id, variable_nombre
        """
        url = f"{self.BASE_URL}/monetarias/{variable_id}"
        params = {'limit': limit}

        if desde:
            params['desde'] = desde
        if hasta:
            params['hasta'] = hasta

        try:
            logger.info(f"Descargando variable {variable_id}...")
            response = self.session.get(url, params=params, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            # Extraer datos del detalle
            if 'results' in data and len(data['results']) > 0:
                detalle = data['results'][0].get('detalle', [])

                if not detalle:
                    logger.warning(f"No hay datos para variable {variable_id}")
                    return pd.DataFrame()

                # Convertir a DataFrame
                df = pd.DataFrame(detalle)

                # Convertir fecha a datetime
                df['fecha'] = pd.to_datetime(df['fecha'])

                # Agregar metadata
                df['variable_id'] = variable_id
                df['variable_nombre'] = self.get_variable_name(variable_id)

                # Ordenar por fecha
                df = df.sort_values('fecha').reset_index(drop=True)

                logger.info(f"   ✓ {len(df):,} registros descargados")

                return df
            else:
                logger.warning(f"No se encontraron resultados para variable {variable_id}")
                return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener variable {variable_id}: {e}")
            raise

    def get_multiple_variables(
        self,
        variable_ids: List[int],
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
        format: str = 'wide'
    ) -> pd.DataFrame:
        """
        Obtiene datos de múltiples variables.

        Args:
            variable_ids: Lista de IDs de variables
            desde: Fecha de inicio en formato YYYY-MM-DD
            hasta: Fecha de fin en formato YYYY-MM-DD
            format: 'wide' (una columna por variable) o 'long' (todas apiladas)

        Returns:
            DataFrame con las series temporales
        """
        dfs = []

        for variable_id in variable_ids:
            try:
                df = self.get_variable_data(variable_id, desde, hasta)
                if not df.empty:
                    dfs.append(df)
            except Exception as e:
                logger.error(f"   ❌ Error en variable {variable_id}: {e}")
                continue

        if not dfs:
            return pd.DataFrame()

        # Concatenar todos los DataFrames
        df_combined = pd.concat(dfs, ignore_index=True)

        if format == 'wide':
            # Pivotar para tener una columna por variable
            df_wide = df_combined.pivot(index='fecha', columns='variable_nombre', values='valor')
            df_wide = df_wide.reset_index()
            return df_wide
        else:
            return df_combined

    def get_variable_name(self, variable_id: int) -> str:
        """
        Obtiene el nombre de una variable por su ID.

        Args:
            variable_id: ID de la variable

        Returns:
            Nombre de la variable o "Variable {id}" si no se encuentra
        """
        all_vars = {**self.VARIABLES_MONETARIAS, **self.VARIABLES_INFLACION}
        return all_vars.get(variable_id, f"Variable {variable_id}")

    def get_variable_metadata(self, variable_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene metadata completa de una variable.

        Args:
            variable_id: ID de la variable

        Returns:
            Dict con metadata o None si no se encuentra
        """
        try:
            all_vars = self.get_all_variables()

            if 'results' in all_vars:
                for var in all_vars['results']:
                    if var.get('idVariable') == variable_id:
                        return var

            logger.warning(f"Variable {variable_id} no encontrada")
            return None

        except Exception as e:
            logger.error(f"Error obteniendo metadata: {e}")
            return None

    def print_available_variables(self):
        """
        Imprime las variables disponibles en formato legible.
        """
        print("\n" + "="*80)
        print("VARIABLES DISPONIBLES - API OFICIAL BCRA")
        print("="*80 + "\n")

        print("MONETARIAS:")
        for id, nombre in self.VARIABLES_MONETARIAS.items():
            print(f"   {id:3} - {nombre}")

        print("\nINFLACIÓN E ÍNDICES:")
        for id, nombre in self.VARIABLES_INFLACION.items():
            print(f"   {id:3} - {nombre}")

        print("\n" + "="*80)


# Función de conveniencia
def download_bcra_data_oficial(
    variable_ids: List[int],
    desde: str = '2019-01-01',
    hasta: Optional[str] = None,
    save_to: Optional[str] = None
) -> pd.DataFrame:
    """
    Función de conveniencia para descargar datos del BCRA.

    Args:
        variable_ids: Lista de IDs de variables
        desde: Fecha de inicio
        hasta: Fecha de fin (default: hoy)
        save_to: Ruta para guardar CSV (opcional)

    Returns:
        DataFrame con los datos
    """
    client = BCRAClientOficial()
    df = client.get_multiple_variables(variable_ids, desde, hasta, format='wide')

    if save_to and not df.empty:
        df.to_csv(save_to, index=False, encoding='utf-8')
        print(f"\n✓ Datos guardados en: {save_to}")

    return df


if __name__ == "__main__":
    # Ejemplo de uso
    client = BCRAClientOficial()

    # Mostrar variables disponibles
    client.print_available_variables()

    # Descargar datos de ejemplo
    print("\n📥 Descargando datos de ejemplo (últimos 30 días)...")
    df = client.get_multiple_variables(
        variable_ids=[1, 5, 7],  # Reservas, TC, BADLAR
        desde=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    )

    print("\n" + "="*80)
    print("DATOS DESCARGADOS")
    print("="*80)
    print(df.head(10))
    print(f"\nTotal registros: {len(df)}")
