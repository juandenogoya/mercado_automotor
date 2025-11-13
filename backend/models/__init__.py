"""
Database models module.
"""
from .base import Base
from .patentamientos import Patentamiento
from .produccion import Produccion
from .bcra_indicadores import BCRAIndicador
from .mercadolibre_listings import MercadoLibreListing
from .indicadores_calculados import IndicadorCalculado
from .ipc import IPC
from .badlar import BADLAR
from .tipo_cambio import TipoCambio

__all__ = [
    "Base",
    "Patentamiento",
    "Produccion",
    "BCRAIndicador",
    "MercadoLibreListing",
    "IndicadorCalculado",
    "IPC",
    "BADLAR",
    "TipoCambio",
]
