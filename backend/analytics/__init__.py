"""
Backend Analytics Module.

Módulos de análisis y cálculo de indicadores para el mercado automotor.
"""

from .indicadores import (
    calcular_tension_demanda,
    calcular_rotacion_stock,
    calcular_accesibilidad_compra,
    calcular_ranking_atencion
)

__all__ = [
    'calcular_tension_demanda',
    'calcular_rotacion_stock',
    'calcular_accesibilidad_compra',
    'calcular_ranking_atencion',
]
