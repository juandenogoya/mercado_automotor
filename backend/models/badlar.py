"""
Modelo para datos de BADLAR (Tasa de Interés) del BCRA.
Publicación: Diaria
Fuente: BCRA API
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Index
from .base import Base, TimestampMixin


class BADLAR(Base, TimestampMixin):
    """
    Tabla de BADLAR (Buenos Aires Deposits of Large Amount Rate).

    Características:
    - Frecuencia: Diaria (días hábiles)
    - Fuente: BCRA
    - Delay: 2-3 días
    - Datos históricos: Desde 2000
    - Unidad: % TNA (Tasa Nominal Anual)
    """

    __tablename__ = "badlar"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Dimensión temporal
    fecha = Column(Date, nullable=False, unique=True, index=True)

    # Valor de la tasa
    tasa = Column(Numeric(10, 4), nullable=False)  # % TNA

    # Metadata
    unidad = Column(String(50), nullable=False, default="% TNA")
    fuente = Column(String(50), nullable=False, default="BCRA")
    descripcion = Column(String(255), nullable=True, default="BADLAR bancos privados")

    # Índices
    __table_args__ = (
        Index("idx_badlar_fecha", "fecha"),
    )

    def __repr__(self):
        return f"<BADLAR(fecha={self.fecha}, tasa={self.tasa}%)>"
