"""
Database models module.
"""
from .base import Base
from .patentamientos import Patentamiento
from .produccion import Produccion
from .bcra_indicadores import BCRAIndicador
from .indicadores_calculados import IndicadorCalculado

__all__ = [
    "Base",
    "Patentamiento",
    "Produccion",
    "BCRAIndicador",
    "IndicadorCalculado",
]
