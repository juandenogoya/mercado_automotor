#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente para API de Series de Tiempo de datos.gob.ar (INDEC).

API Docs: https://datosgobar.github.io/series-tiempo-ar-api/
Base URL: https://apis.datos.gob.ar/series/api/

Variables disponibles:
- EMAE: Estimador Mensual de Actividad Económica (mensual)
- Desocupación: Tasa de desempleo (trimestral)
- Tasa de Actividad: (trimestral)
- Tasa de Empleo: (trimestral)
- IPC: Índice de Precios al Consumidor (mensual) - también en BCRA
- Salarios: RIPTE (mensual)
- Construcción: Índice de Construcción (mensual)

Uso:
    from backend.external_apis.indec_client import INDECClient

    client = INDECClient()

    # Obtener una serie
    df = client.get_series_data('EMAE', start_date='2020-01-01')

    # Obtener múltiples series
    df_multiple = client.get_multiple_series(
        series_keys=['EMAE', 'DESOCUPACION', 'ACTIVIDAD'],
        start_date='2020-01-01'
    )
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class INDECClient:
    """Cliente para API de Series de Tiempo de datos.gob.ar"""

    BASE_URL = "https://apis.datos.gob.ar/series/api"

    # Series IDs para indicadores económicos
    SERIES_IDS = {
        # ===== MENSUALES (las mejores para forecasting) =====
        'EMAE': '143.3_NO_PR_2004_A_21',  # Estimador Mensual de Actividad Económica
        'IPC': '148.3_INIVELNAL_DICI_M_26',  # IPC Nivel General (también en BCRA)

        # ===== TRIMESTRALES (EPH Continua) =====
        'DESOCUPACION': '45.2_ECTDT_0_T_33',  # Tasa de desocupación
        'ACTIVIDAD': '43.2_ECTAT_0_T_33',  # Tasa de actividad
        'EMPLEO': '44.2_ECTET_0_T_30',  # Tasa de empleo

        # ===== ADICIONALES =====
        'SALARIOS': '158.1_REPTE_0_0_5',  # RIPTE - Remuneración Imponible Promedio
        'CONSTRUCCION': None,  # Índice Construcción - buscar ID
        'VENTAS_SUPER': None,  # Ventas en supermercados - buscar ID
    }

    # Mapeo de nombres amigables
    VARIABLE_NAMES = {
        'EMAE': 'EMAE - Estimador Mensual de Actividad Económica',
        'IPC': 'IPC Nivel General',
        'DESOCUPACION': 'Tasa de Desocupación',
        'ACTIVIDAD': 'Tasa de Actividad',
        'EMPLEO': 'Tasa de Empleo',
        'SALARIOS': 'RIPTE - Remuneración Imponible Promedio',
        'CONSTRUCCION': 'Índice de Construcción',
        'VENTAS_SUPER': 'Ventas en Supermercados'
    }

    # Frecuencia de cada serie
    FRECUENCIAS = {
        'EMAE': 'M',  # Mensual
        'IPC': 'M',
        'DESOCUPACION': 'Q',  # Trimestral
        'ACTIVIDAD': 'Q',
        'EMPLEO': 'Q',
        'SALARIOS': 'M',
        'CONSTRUCCION': 'M',
        'VENTAS_SUPER': 'M'
    }

    def __init__(self, timeout: int = 30):
        """
        Inicializa el cliente INDEC.

        Args:
            timeout: Timeout para requests (segundos)
        """
        self.timeout = timeout
        self.session = requests.Session()

    def get_series_data(
        self,
        series_key: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        format: str = 'json'
    ) -> pd.DataFrame:
        """
        Obtiene datos de una serie temporal.

        Args:
            series_key: Clave de la serie (ej: 'EMAE', 'DESOCUPACION')
            start_date: Fecha de inicio (formato YYYY-MM-DD)
            end_date: Fecha de fin (formato YYYY-MM-DD)
            format: Formato de respuesta ('json' o 'csv')

        Returns:
            DataFrame con columnas: fecha, valor, serie
        """
        # Obtener ID de la serie
        series_id = self.SERIES_IDS.get(series_key)

        if series_id is None:
            logger.warning(f"Serie '{series_key}' no tiene ID configurado")
            return pd.DataFrame()

        try:
            url = f"{self.BASE_URL}/series"

            params = {
                'ids': series_id,
                'format': format
            }

            if start_date:
                params['start_date'] = start_date

            if end_date:
                params['end_date'] = end_date

            logger.info(f"📥 Descargando: {series_key} ({series_id})")

            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )

            response.raise_for_status()

            if format == 'json':
                data = response.json()

                # Extraer datos
                if 'data' in data and len(data['data']) > 0:
                    df = pd.DataFrame(data['data'])

                    # La API devuelve columnas: [fecha, valor1, valor2, ...]
                    # Primera columna es fecha, segunda es el valor
                    df.columns = ['fecha'] + [f'valor_{i}' for i in range(len(df.columns) - 1)]

                    # Renombrar primera columna de valor a 'valor'
                    if 'valor_0' in df.columns:
                        df = df.rename(columns={'valor_0': 'valor'})

                    # Convertir fecha a datetime
                    df['fecha'] = pd.to_datetime(df['fecha'])

                    # Agregar metadata
                    df['serie'] = series_key
                    df['frecuencia'] = self.FRECUENCIAS.get(series_key, 'U')

                    # Seleccionar solo columnas relevantes
                    df = df[['fecha', 'valor', 'serie', 'frecuencia']]

                    # Ordenar por fecha
                    df = df.sort_values('fecha').reset_index(drop=True)

                    logger.info(f"   ✓ {len(df):,} registros descargados")

                    return df
                else:
                    logger.warning(f"   ⚠️  No hay datos para {series_key}")
                    return pd.DataFrame()
            else:
                logger.warning("Formato CSV no implementado completamente")
                return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            logger.error(f"   ❌ Error consultando {series_key}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"   ❌ Error inesperado en {series_key}: {e}")
            return pd.DataFrame()

    def get_multiple_series(
        self,
        series_keys: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        format: str = 'wide'
    ) -> pd.DataFrame:
        """
        Obtiene múltiples series temporales.

        Args:
            series_keys: Lista de claves de series (ej: ['EMAE', 'DESOCUPACION'])
            start_date: Fecha de inicio
            end_date: Fecha de fin
            format: 'wide' (una columna por serie) o 'long' (todas apiladas)

        Returns:
            DataFrame con las series temporales
        """
        dfs = []

        for series_key in series_keys:
            try:
                df = self.get_series_data(series_key, start_date, end_date)
                if not df.empty:
                    dfs.append(df)
            except Exception as e:
                logger.error(f"Error obteniendo {series_key}: {e}")
                continue

        if not dfs:
            return pd.DataFrame()

        # Concatenar todos los DataFrames
        df_combined = pd.concat(dfs, ignore_index=True)

        if format == 'wide':
            # Pivotar para tener una columna por serie
            df_wide = df_combined.pivot(index='fecha', columns='serie', values='valor')
            df_wide = df_wide.reset_index()
            return df_wide
        else:
            return df_combined

    def search_series(self, query: str, limit: int = 10) -> pd.DataFrame:
        """
        Busca series por texto.

        Args:
            query: Texto a buscar (ej: 'salario', 'construccion')
            limit: Máximo de resultados

        Returns:
            DataFrame con series encontradas
        """
        try:
            url = f"{self.BASE_URL}/search"

            params = {
                'q': query,
                'limit': limit
            }

            logger.info(f"🔍 Buscando series con: '{query}'")

            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if 'data' in data and len(data['data']) > 0:
                df = pd.DataFrame(data['data'])
                logger.info(f"   ✓ {len(df)} series encontradas")
                return df
            else:
                logger.warning("   ⚠️  No se encontraron series")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"   ❌ Error en búsqueda: {e}")
            return pd.DataFrame()

    def get_info(self) -> Dict[str, str]:
        """
        Obtiene información sobre las series disponibles.

        Returns:
            Diccionario con series y sus descripciones
        """
        return self.VARIABLE_NAMES.copy()

    def print_available_series(self):
        """
        Imprime las series disponibles en formato legible.
        """
        print("\n" + "="*80)
        print("SERIES DISPONIBLES - INDEC (datos.gob.ar)")
        print("="*80 + "\n")

        print("MENSUALES:")
        for key, name in self.VARIABLE_NAMES.items():
            if self.FRECUENCIAS.get(key) == 'M' and self.SERIES_IDS.get(key):
                series_id = self.SERIES_IDS[key]
                print(f"   {key:15} - {name:50} ({series_id})")

        print("\nTRIMESTRALES:")
        for key, name in self.VARIABLE_NAMES.items():
            if self.FRECUENCIAS.get(key) == 'Q' and self.SERIES_IDS.get(key):
                series_id = self.SERIES_IDS[key]
                print(f"   {key:15} - {name:50} ({series_id})")

        print("\nPENDIENTES DE BUSCAR ID:")
        for key, name in self.VARIABLE_NAMES.items():
            if self.SERIES_IDS.get(key) is None:
                print(f"   {key:15} - {name}")

        print("\n" + "="*80)


# Función de conveniencia
def download_indec_data(
    series_keys: List[str],
    start_date: str = '2019-01-01',
    end_date: Optional[str] = None,
    save_to: Optional[str] = None
) -> pd.DataFrame:
    """
    Función de conveniencia para descargar datos de INDEC.

    Args:
        series_keys: Lista de claves de series
        start_date: Fecha de inicio
        end_date: Fecha de fin (default: hoy)
        save_to: Ruta para guardar CSV (opcional)

    Returns:
        DataFrame con los datos
    """
    client = INDECClient()
    df = client.get_multiple_series(series_keys, start_date, end_date, format='wide')

    if save_to and not df.empty:
        df.to_csv(save_to, index=False, encoding='utf-8')
        print(f"\n✓ Datos guardados en: {save_to}")

    return df


if __name__ == "__main__":
    # Ejemplo de uso
    client = INDECClient()

    # Mostrar series disponibles
    client.print_available_series()

    # Descargar datos de ejemplo
    print("\n📥 Descargando datos de ejemplo (últimos 12 meses)...")
    df = client.get_multiple_series(
        series_keys=['EMAE', 'DESOCUPACION', 'ACTIVIDAD'],
        start_date=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    )

    print("\n" + "="*80)
    print("DATOS DESCARGADOS")
    print("="*80)
    print(df.head(10))
    print(f"\nTotal registros: {len(df)}")
