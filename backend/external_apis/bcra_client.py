#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente para la API del BCRA (Banco Central de la República Argentina).

API utilizada: https://api.estadisticasbcra.com/
Documentación: https://estadisticasbcra.com/api/documentacion

Variables disponibles:
- reservas: Reservas internacionales (en millones de USD)
- usd: Tipo de cambio USD oficial
- usd_of: Tipo de cambio USD informal (blue)
- base_monetaria: Base monetaria (en millones de pesos)
- circulacion_monetaria: Circulación monetaria
- depositos: Depósitos totales
- plazo_fijo: Depósitos a plazo fijo
- tasa_badlar: Tasa BADLAR (%)
- tasa_leliq: Tasa LELIQ (%)
- inflacion_mensual_oficial: IPC mensual (%)
- inflacion_interanual_oficial: IPC interanual (%)
- var_usd_vs_usd_of: Spread entre dólar oficial y blue

Uso:
    from backend.external_apis.bcra_client import BCRAClient

    client = BCRAClient()

    # Obtener datos de una variable
    df = client.get_series('usd', fecha_desde='2020-01-01', fecha_hasta='2025-12-31')

    # Obtener múltiples variables
    df_multiple = client.get_multiple_series(
        variables=['usd', 'inflacion_mensual_oficial', 'tasa_badlar'],
        fecha_desde='2020-01-01'
    )
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import time


class BCRAClient:
    """
    Cliente para acceder a la API del BCRA.
    """

    BASE_URL = "https://api.estadisticasbcra.com"

    # Variables disponibles y sus descripciones
    VARIABLES_DISPONIBLES = {
        'reservas': 'Reservas Internacionales (millones USD)',
        'usd': 'Tipo de Cambio USD Oficial',
        'usd_of': 'Tipo de Cambio USD Informal',
        'base_monetaria': 'Base Monetaria (millones ARS)',
        'circulacion_monetaria': 'Circulación Monetaria',
        'depositos': 'Depósitos Totales',
        'plazo_fijo': 'Depósitos a Plazo Fijo',
        'tasa_badlar': 'Tasa BADLAR (%)',
        'tasa_leliq': 'Tasa LELIQ (%)',
        'inflacion_mensual_oficial': 'IPC Mensual (%)',
        'inflacion_interanual_oficial': 'IPC Interanual (%)',
        'var_usd_vs_usd_of': 'Spread USD Oficial vs Informal (%)'
    }

    def __init__(self, bearer_token: Optional[str] = None, timeout: int = 30):
        """
        Inicializa el cliente BCRA.

        Args:
            bearer_token: Token de autenticación (opcional, la API pública no lo requiere)
            timeout: Timeout para las requests (segundos)
        """
        self.bearer_token = bearer_token
        self.timeout = timeout
        self.session = requests.Session()

        if bearer_token:
            self.session.headers.update({
                'Authorization': f'Bearer {bearer_token}'
            })

    def get_series(
        self,
        variable: str,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        max_retries: int = 3
    ) -> pd.DataFrame:
        """
        Obtiene datos de una serie temporal del BCRA.

        Args:
            variable: Nombre de la variable (ej: 'usd', 'inflacion_mensual_oficial')
            fecha_desde: Fecha de inicio en formato 'YYYY-MM-DD' (default: 1 año atrás)
            fecha_hasta: Fecha de fin en formato 'YYYY-MM-DD' (default: hoy)
            max_retries: Número máximo de reintentos en caso de fallo

        Returns:
            DataFrame con columnas: fecha, valor

        Raises:
            ValueError: Si la variable no es válida
            requests.exceptions.RequestException: Si falla la request después de los reintentos
        """
        # Validar variable
        if variable not in self.VARIABLES_DISPONIBLES:
            raise ValueError(
                f"Variable '{variable}' no válida. "
                f"Variables disponibles: {list(self.VARIABLES_DISPONIBLES.keys())}"
            )

        # Fechas por defecto
        if fecha_hasta is None:
            fecha_hasta = datetime.now().strftime('%Y-%m-%d')

        if fecha_desde is None:
            fecha_desde = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # Construir URL
        url = f"{self.BASE_URL}/{variable}"
        params = {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        }

        # Realizar request con reintentos
        for intento in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()

                # Parsear JSON
                data = response.json()

                # Convertir a DataFrame
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)

                    # Renombrar columnas (la API devuelve 'd' para fecha, 'v' para valor)
                    if 'd' in df.columns and 'v' in df.columns:
                        df = df.rename(columns={'d': 'fecha', 'v': 'valor'})

                    # Convertir fecha a datetime
                    df['fecha'] = pd.to_datetime(df['fecha'])

                    # Convertir valor a numérico
                    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')

                    # Agregar columna con nombre de variable
                    df['variable'] = variable

                    # Ordenar por fecha
                    df = df.sort_values('fecha').reset_index(drop=True)

                    return df
                else:
                    return pd.DataFrame(columns=['fecha', 'valor', 'variable'])

            except requests.exceptions.RequestException as e:
                if intento < max_retries - 1:
                    wait_time = 2 ** intento  # Exponential backoff
                    print(f"⚠️  Error en intento {intento + 1}/{max_retries}: {e}")
                    print(f"   Reintentando en {wait_time} segundos...")
                    time.sleep(wait_time)
                else:
                    raise

    def get_multiple_series(
        self,
        variables: List[str],
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        format: str = 'wide'
    ) -> pd.DataFrame:
        """
        Obtiene múltiples series temporales del BCRA.

        Args:
            variables: Lista de nombres de variables
            fecha_desde: Fecha de inicio en formato 'YYYY-MM-DD'
            fecha_hasta: Fecha de fin en formato 'YYYY-MM-DD'
            format: 'wide' (una columna por variable) o 'long' (todas apiladas)

        Returns:
            DataFrame con las series temporales
        """
        dfs = []

        for variable in variables:
            print(f"📥 Descargando: {variable}...")
            try:
                df = self.get_series(variable, fecha_desde, fecha_hasta)
                dfs.append(df)
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

        if not dfs:
            return pd.DataFrame()

        # Concatenar todos los DataFrames
        df_combined = pd.concat(dfs, ignore_index=True)

        if format == 'wide':
            # Pivotar para tener una columna por variable
            df_wide = df_combined.pivot(index='fecha', columns='variable', values='valor')
            df_wide = df_wide.reset_index()
            return df_wide
        else:
            return df_combined

    def get_latest_value(self, variable: str) -> Optional[float]:
        """
        Obtiene el último valor disponible de una variable.

        Args:
            variable: Nombre de la variable

        Returns:
            Último valor disponible o None si no hay datos
        """
        df = self.get_series(variable, fecha_desde=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))

        if not df.empty:
            return df.iloc[-1]['valor']
        return None

    def get_info(self) -> Dict[str, str]:
        """
        Obtiene información sobre las variables disponibles.

        Returns:
            Diccionario con variables y sus descripciones
        """
        return self.VARIABLES_DISPONIBLES.copy()

    def print_available_variables(self):
        """
        Imprime las variables disponibles en formato legible.
        """
        print("\n" + "="*80)
        print("VARIABLES DISPONIBLES EN API BCRA")
        print("="*80 + "\n")

        for i, (var, desc) in enumerate(self.VARIABLES_DISPONIBLES.items(), 1):
            print(f"{i:2}. {var:30} - {desc}")

        print("\n" + "="*80)


# Función de conveniencia
def download_bcra_data(
    variables: List[str],
    fecha_desde: str = '2019-01-01',
    fecha_hasta: Optional[str] = None,
    save_to: Optional[str] = None
) -> pd.DataFrame:
    """
    Función de conveniencia para descargar datos del BCRA.

    Args:
        variables: Lista de variables a descargar
        fecha_desde: Fecha de inicio
        fecha_hasta: Fecha de fin (default: hoy)
        save_to: Ruta para guardar CSV (opcional)

    Returns:
        DataFrame con los datos
    """
    client = BCRAClient()
    df = client.get_multiple_series(variables, fecha_desde, fecha_hasta, format='wide')

    if save_to and not df.empty:
        df.to_csv(save_to, index=False, encoding='utf-8')
        print(f"\n✓ Datos guardados en: {save_to}")

    return df


if __name__ == "__main__":
    # Ejemplo de uso
    client = BCRAClient()

    # Mostrar variables disponibles
    client.print_available_variables()

    # Descargar datos de ejemplo
    print("\n📥 Descargando datos de ejemplo (últimos 30 días)...")
    df = client.get_multiple_series(
        variables=['usd', 'inflacion_mensual_oficial', 'tasa_badlar'],
        fecha_desde=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    )

    print("\n" + "="*80)
    print("DATOS DESCARGADOS")
    print("="*80)
    print(df.head(10))
    print(f"\nTotal registros: {len(df)}")
