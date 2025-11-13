"""
Modelo para IPC expandido a frecuencia diaria.
"""
from sqlalchemy import Column, Integer, Date, Numeric, String, Index
from .base import Base, TimestampMixin


class IPCDiario(Base, TimestampMixin):
    """
    Tabla de IPC expandido a frecuencia diaria (usando período de vigencia).

    Lógica de expansión (Opción B - Vigencia):
    - IPC Septiembre 2024 = 2.5%
    - Se aplica TODO octubre 2024 (1-31 octubre)
    - Cada día de octubre tiene el valor 2.5%

    Características:
    - Frecuencia: Diaria
    - Fuente: INDEC (transformado)
    """

    __tablename__ = "ipc_diario"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Fecha del día (frecuencia diaria)
    fecha = Column(Date, nullable=False, unique=True, index=True)

    # Valor del IPC mensual aplicado
    ipc_mensual = Column(Numeric(10, 4), nullable=False)  # % variación mensual

    # Metadata para trazabilidad
    periodo_medido = Column(Date, nullable=False)  # Mes que midió (ej: sept 2024)
    periodo_vigencia = Column(Date, nullable=False, index=True)  # Mes que se aplica (ej: oct 2024)

    # Utilidades adicionales
    dias_desde_publicacion = Column(Integer, nullable=True)  # Días desde que se publicó
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)

    # Fuente
    fuente = Column(String(50), nullable=False, default="INDEC_DIARIO")

    # Índices
    __table_args__ = (
        Index("idx_ipc_diario_fecha", "fecha"),
        Index("idx_ipc_diario_periodo_vigencia", "periodo_vigencia"),
        Index("idx_ipc_diario_anio_mes", "anio", "mes"),
    )

    def __repr__(self):
        return f"<IPCDiario(fecha={self.fecha}, ipc={self.ipc_mensual}%, vigencia={self.periodo_vigencia})>"
