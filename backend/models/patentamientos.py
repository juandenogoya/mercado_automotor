"""
Modelo para datos de patentamientos (ACARA/FACCARA).
"""
from sqlalchemy import Column, Integer, String, Date, Index
from .base import Base, TimestampMixin


class Patentamiento(Base, TimestampMixin):
    """
    Tabla de patentamientos de vehículos 0km y transferencias de usados.
    Fuente: ACARA/FACCARA
    """

    __tablename__ = "patentamientos"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Dimensiones temporales
    fecha = Column(Date, nullable=False, index=True)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)

    # Dimensiones del vehículo
    tipo_vehiculo = Column(String(50), nullable=False)  # '0km', 'usado'
    marca = Column(String(100), nullable=True)
    modelo = Column(String(100), nullable=True)
    segmento = Column(String(50), nullable=True)  # 'sedan', 'suv', 'pickup', etc.

    # Métricas
    cantidad = Column(Integer, nullable=False)

    # Metadata
    fuente = Column(String(50), nullable=False, default="ACARA")  # 'ACARA', 'FACCARA'
    periodo_reportado = Column(String(20), nullable=False)  # 'YYYY-MM'

    # Índices compuestos para optimizar queries
    __table_args__ = (
        Index("idx_patentamientos_fecha_marca", "fecha", "marca"),
        Index("idx_patentamientos_tipo_fecha", "tipo_vehiculo", "fecha"),
        Index("idx_patentamientos_periodo", "periodo_reportado"),
    )

    def __repr__(self):
        return f"<Patentamiento(fecha={self.fecha}, marca={self.marca}, tipo={self.tipo_vehiculo}, cantidad={self.cantidad})>"
