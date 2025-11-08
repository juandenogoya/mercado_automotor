"""
Modelo para indicadores calculados/agregados.
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, JSON, Index
from .base import Base, TimestampMixin


class IndicadorCalculado(Base, TimestampMixin):
    """
    Tabla de indicadores calculados a partir de múltiples fuentes.

    Ejemplos:
    - Índice de tensión de demanda
    - Rotación estimada por terminal
    - Índice de accesibilidad de compra
    - Ranking de atención de marca
    """

    __tablename__ = "indicadores_calculados"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Dimensiones temporales
    fecha = Column(Date, nullable=False, index=True)
    periodo = Column(String(20), nullable=False)  # 'YYYY-MM'

    # Tipo de indicador
    indicador = Column(String(100), nullable=False, index=True)
    # Ejemplos:
    # - 'tension_demanda'
    # - 'rotacion_stock'
    # - 'accesibilidad_compra'
    # - 'ranking_atencion'

    # Dimensiones adicionales (opcional)
    marca = Column(String(100), nullable=True, index=True)
    segmento = Column(String(50), nullable=True)

    # Valor del indicador
    valor = Column(Numeric(18, 4), nullable=False)

    # Detalles adicionales en JSON
    detalles = Column(JSON, nullable=True)
    # Ejemplo: {"componentes": {"acara": 0.5, "bcra": -0.3}, "confianza": 0.85}

    # Metadata
    descripcion = Column(String(255), nullable=True)
    unidad = Column(String(50), nullable=True)

    # Índices
    __table_args__ = (
        Index("idx_indicador_fecha_tipo", "fecha", "indicador"),
        Index("idx_indicador_marca", "marca", "indicador"),
    )

    def __repr__(self):
        return f"<IndicadorCalculado(fecha={self.fecha}, indicador={self.indicador}, valor={self.valor})>"
