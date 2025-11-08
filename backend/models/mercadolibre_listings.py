"""
Modelo para listados de MercadoLibre.
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, Text, Index
from .base import Base, TimestampMixin


class MercadoLibreListing(Base, TimestampMixin):
    """
    Tabla de listados de vehículos en MercadoLibre.
    Fuente: API MercadoLibre
    """

    __tablename__ = "mercadolibre_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ID único de MercadoLibre
    meli_id = Column(String(50), nullable=False, unique=True, index=True)

    # Fecha del snapshot
    fecha_snapshot = Column(Date, nullable=False, index=True)

    # Información del vehículo
    marca = Column(String(100), nullable=True, index=True)
    modelo = Column(String(100), nullable=True)
    anio = Column(Integer, nullable=True)
    kilometros = Column(Integer, nullable=True)
    combustible = Column(String(50), nullable=True)

    # Precio
    precio = Column(Numeric(18, 2), nullable=False)
    moneda = Column(String(10), nullable=False, default="ARS")

    # Ubicación
    provincia = Column(String(100), nullable=True)
    ciudad = Column(String(100), nullable=True)

    # Estado del listing
    estado = Column(String(50), nullable=True)  # 'active', 'paused', 'closed', etc.
    condicion = Column(String(20), nullable=True)  # 'new', 'used'

    # Engagement
    visitas = Column(Integer, nullable=True, default=0)
    ventas = Column(Integer, nullable=True, default=0)

    # Metadata
    titulo = Column(String(255), nullable=True)
    descripcion = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    es_nuevo = Column(Boolean, nullable=True)

    # Índices
    __table_args__ = (
        Index("idx_meli_fecha_marca", "fecha_snapshot", "marca"),
        Index("idx_meli_precio", "precio"),
    )

    def __repr__(self):
        return f"<MercadoLibreListing(meli_id={self.meli_id}, marca={self.marca}, precio={self.precio})>"
