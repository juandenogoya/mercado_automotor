"""
Modelo para datos de Tipo de Cambio del BCRA.
Publicación: Diaria
Fuente: BCRA API
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Index
from .base import Base, TimestampMixin


class TipoCambio(Base, TimestampMixin):
    """
    Tabla de Tipo de Cambio (USD/ARS).

    Características:
    - Frecuencia: Diaria (días hábiles)
    - Fuente: BCRA
    - Delay: 2-3 días
    - Datos históricos: Desde 2000
    - Tipos: Mayorista (Referencia BNA)
    """

    __tablename__ = "tipo_cambio"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Dimensión temporal
    fecha = Column(Date, nullable=False, index=True)

    # Tipo de cotización
    tipo = Column(String(50), nullable=False, default="mayorista")  # 'mayorista', 'minorista', etc.

    # Valores
    compra = Column(Numeric(10, 4), nullable=True)  # Precio compra
    venta = Column(Numeric(10, 4), nullable=True)  # Precio venta
    promedio = Column(Numeric(10, 4), nullable=False)  # Precio promedio/referencia

    # Metadata
    moneda = Column(String(10), nullable=False, default="USD")
    fuente = Column(String(50), nullable=False, default="BCRA")
    descripcion = Column(String(255), nullable=True, default="Tipo de cambio mayorista (Referencia BNA)")

    # Índices
    __table_args__ = (
        Index("idx_tc_fecha_tipo", "fecha", "tipo"),
        Index("idx_tc_fecha", "fecha"),
    )

    def __repr__(self):
        return f"<TipoCambio(fecha={self.fecha}, tipo={self.tipo}, promedio={self.promedio})>"
