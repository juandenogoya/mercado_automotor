"""
Modelo para datos de IPC (Índice de Precios al Consumidor) del INDEC.
Publicación: Mensual
Fuente: INDEC API
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Index
from .base import Base, TimestampMixin


class IPC(Base, TimestampMixin):
    """
    Tabla de IPC (Índice de Precios al Consumidor).

    Características:
    - Frecuencia: Mensual
    - Fuente: INDEC
    - Delay: ~15 días del mes siguiente
    - Datos históricos: Desde 2016
    """

    __tablename__ = "ipc"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Dimensión temporal
    fecha = Column(Date, nullable=False, unique=True, index=True)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)

    # Valores del IPC
    nivel_general = Column(Numeric(18, 4), nullable=False)  # Índice base
    variacion_mensual = Column(Numeric(10, 4), nullable=True)  # % mes vs mes anterior
    variacion_interanual = Column(Numeric(10, 4), nullable=True)  # % mes vs mismo mes año anterior
    variacion_acumulada = Column(Numeric(10, 4), nullable=True)  # % acumulada del año

    # Metadata
    fuente = Column(String(50), nullable=False, default="INDEC")
    periodo_reportado = Column(String(20), nullable=False)  # 'YYYY-MM'

    # Índices
    __table_args__ = (
        Index("idx_ipc_anio_mes", "anio", "mes"),
        Index("idx_ipc_periodo", "periodo_reportado"),
    )

    def __repr__(self):
        return f"<IPC(fecha={self.fecha}, nivel={self.nivel_general}, var_mensual={self.variacion_mensual}%)>"
