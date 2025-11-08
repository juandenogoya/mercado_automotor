"""
Modelo para datos de producción (ADEFA).
"""
from sqlalchemy import Column, Integer, String, Date, Index
from .base import Base, TimestampMixin


class Produccion(Base, TimestampMixin):
    """
    Tabla de producción nacional de vehículos.
    Fuente: ADEFA
    """

    __tablename__ = "produccion"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Dimensiones temporales
    fecha = Column(Date, nullable=False, index=True)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)

    # Dimensiones del vehículo
    terminal = Column(String(100), nullable=True)  # Marca/fabricante
    modelo = Column(String(100), nullable=True)
    segmento = Column(String(50), nullable=True)

    # Métricas
    unidades_producidas = Column(Integer, nullable=False, default=0)
    unidades_exportadas = Column(Integer, nullable=False, default=0)

    # Metadata
    fuente = Column(String(50), nullable=False, default="ADEFA")
    periodo_reportado = Column(String(20), nullable=False)  # 'YYYY-MM'

    # Índices
    __table_args__ = (
        Index("idx_produccion_fecha_terminal", "fecha", "terminal"),
        Index("idx_produccion_periodo", "periodo_reportado"),
    )

    def __repr__(self):
        return f"<Produccion(fecha={self.fecha}, terminal={self.terminal}, producidas={self.unidades_producidas})>"
