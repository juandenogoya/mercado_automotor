"""
Modelo para indicadores del BCRA.
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Index
from .base import Base, TimestampMixin


class BCRAIndicador(Base, TimestampMixin):
    """
    Tabla de indicadores económicos del BCRA.
    Fuente: API BCRA
    """

    __tablename__ = "bcra_indicadores"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Dimensiones temporales
    fecha = Column(Date, nullable=False, index=True)

    # Tipo de indicador
    indicador = Column(String(100), nullable=False, index=True)
    # Ejemplos: 'tasa_badlar', 'tasa_plazo_fijo', 'creditos_prendarios',
    #           'tipo_cambio', 'reservas_internacionales', etc.

    # Valor del indicador
    valor = Column(Numeric(18, 4), nullable=False)

    # Unidad de medida
    unidad = Column(String(50), nullable=True)  # '%', 'millones ARS', 'USD', etc.

    # Metadata
    fuente = Column(String(50), nullable=False, default="BCRA")
    descripcion = Column(String(255), nullable=True)

    # Índices
    __table_args__ = (
        Index("idx_bcra_fecha_indicador", "fecha", "indicador"),
    )

    def __repr__(self):
        return f"<BCRAIndicador(fecha={self.fecha}, indicador={self.indicador}, valor={self.valor})>"
