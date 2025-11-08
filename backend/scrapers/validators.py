"""
Validadores Pydantic para datos scrapeados.

Aseguran que los datos extraídos cumplan con el esquema esperado
antes de insertarse en la base de datos.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, validator, ConfigDict
from loguru import logger


class PatentamientoData(BaseModel):
    """Validador para datos de patentamientos de ACARA/FACCARA/DNRPA."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    fecha: date
    anio: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    tipo_vehiculo: str
    marca: str
    cantidad: int = Field(..., ge=0, le=1000000)
    fuente: str
    periodo_reportado: str
    modelo: Optional[str] = None
    provincia: Optional[str] = None  # Para datos de DNRPA

    @validator('tipo_vehiculo')
    def validate_tipo(cls, v):
        """Valida que tipo_vehiculo sea válido."""
        valid_types = ['0km', 'usado']
        if v not in valid_types:
            raise ValueError(f"tipo_vehiculo debe ser uno de {valid_types}, recibido: {v}")
        return v

    @validator('marca')
    def validate_marca(cls, v):
        """Valida que marca no esté vacía y tenga formato correcto."""
        if not v or v.strip() == '':
            raise ValueError("marca no puede estar vacía")

        # Normalizar marca
        v = v.strip().title()

        # Lista de marcas conocidas (puede extenderse)
        marcas_conocidas = {
            'Toyota', 'Ford', 'Chevrolet', 'Volkswagen', 'Fiat', 'Renault',
            'Peugeot', 'Nissan', 'Honda', 'Jeep', 'Ram', 'Citroën', 'Hyundai',
            'Kia', 'Mercedes-Benz', 'BMW', 'Audi', 'Volvo', 'Iveco', 'Scania',
            'Chery', 'Dfsk', 'Geely', 'Haval', 'Jac', 'Lifan', 'Mahindra',
            'Otras', 'Total', 'Otros'
        }

        # Advertencia si no es marca conocida (pero no falla)
        if v not in marcas_conocidas:
            logger.warning(f"Marca no reconocida: {v}")

        return v

    @validator('fuente')
    def validate_fuente(cls, v):
        """Valida que la fuente sea válida."""
        valid_sources = ['ACARA', 'FACCARA', 'DNRPA']
        if v not in valid_sources:
            raise ValueError(f"fuente debe ser uno de {valid_sources}")
        return v

    @validator('fecha')
    def validate_fecha(cls, v):
        """Valida que la fecha no sea futura."""
        if v > date.today():
            raise ValueError(f"fecha no puede ser futura: {v}")
        return v

    @validator('cantidad')
    def validate_cantidad_realista(cls, v):
        """Valida que la cantidad sea realista."""
        # Argentina patentan ~30-50k vehículos/mes en total
        # Por marca, el máximo realista sería ~15k/mes
        if v > 50000:
            logger.warning(f"Cantidad muy alta (posible error): {v}")
        return v


class ProduccionData(BaseModel):
    """Validador para datos de producción de ADEFA."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    fecha: date
    anio: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    terminal: str
    unidades_producidas: int = Field(..., ge=0, le=1000000)
    unidades_exportadas: int = Field(..., ge=0, le=1000000)
    fuente: str
    periodo_reportado: str

    @validator('terminal')
    def validate_terminal(cls, v):
        """Valida que terminal no esté vacía."""
        if not v or v.strip() == '':
            raise ValueError("terminal no puede estar vacía")

        # Normalizar terminal
        v = v.strip().title()

        # Terminales conocidas en Argentina
        terminales_conocidas = {
            'Toyota', 'Ford', 'Volkswagen', 'Fiat', 'Renault', 'Peugeot-Citroën',
            'General Motors', 'Nissan', 'Honda', 'Mercedes-Benz', 'Iveco', 'Scania',
            'Volvo', 'Total', 'Otras'
        }

        if v not in terminales_conocidas:
            logger.warning(f"Terminal no reconocida: {v}")

        return v

    @validator('fuente')
    def validate_fuente(cls, v):
        """Valida que la fuente sea ADEFA."""
        if v != 'ADEFA':
            raise ValueError(f"fuente debe ser 'ADEFA', recibido: {v}")
        return v

    @validator('unidades_exportadas')
    def validate_exportadas_vs_producidas(cls, v, values):
        """Valida que exportadas no supere producidas."""
        if 'unidades_producidas' in values:
            if v > values['unidades_producidas']:
                logger.warning(
                    f"Exportadas ({v}) > Producidas ({values['unidades_producidas']}) "
                    f"para {values.get('terminal', 'N/A')}"
                )
        return v

    @validator('fecha')
    def validate_fecha(cls, v):
        """Valida que la fecha no sea futura."""
        if v > date.today():
            raise ValueError(f"fecha no puede ser futura: {v}")
        return v


class BCRAIndicadorData(BaseModel):
    """Validador para datos de indicadores del BCRA."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    fecha: date
    indicador: str
    valor: float
    unidad: Optional[str] = None

    @validator('indicador')
    def validate_indicador(cls, v):
        """Valida que el indicador sea conocido."""
        indicadores_conocidos = {
            'BADLAR', 'tasa_pf', 'tipo_cambio', 'reservas', 'creditos_prendarios',
            'base_monetaria', 'circulacion_monetaria', 'depositos', 'prestamos'
        }

        if v not in indicadores_conocidos:
            logger.warning(f"Indicador no reconocido: {v}")

        return v

    @validator('valor')
    def validate_valor(cls, v, values):
        """Valida que el valor sea razonable según el indicador."""
        indicador = values.get('indicador', '')

        # Validaciones específicas por indicador
        if 'tasa' in indicador.lower():
            if v < 0 or v > 500:  # Tasas entre 0% y 500%
                raise ValueError(f"Tasa fuera de rango razonable: {v}%")

        elif 'tipo_cambio' in indicador.lower():
            if v < 0 or v > 10000:  # Tipo de cambio entre 0 y 10000
                raise ValueError(f"Tipo de cambio fuera de rango: {v}")

        elif 'reservas' in indicador.lower():
            if v < -100000 or v > 1000000:  # Reservas en millones USD
                logger.warning(f"Reservas fuera de rango típico: {v}M USD")

        return v

    @validator('fecha')
    def validate_fecha(cls, v):
        """Valida que la fecha no sea futura."""
        if v > date.today():
            raise ValueError(f"fecha no puede ser futura: {v}")
        return v


class MercadoLibreListingData(BaseModel):
    """Validador para datos de listados de MercadoLibre."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    meli_id: str
    marca: str
    modelo: Optional[str] = None
    anio: Optional[int] = Field(None, ge=1950, le=2100)
    precio: float = Field(..., gt=0)
    moneda: str
    condicion: str
    kilometros: Optional[int] = Field(None, ge=0)
    combustible: Optional[str] = None
    transmision: Optional[str] = None
    ubicacion: Optional[str] = None
    url: str
    fecha_snapshot: date

    @validator('meli_id')
    def validate_meli_id(cls, v):
        """Valida formato de ID de MercadoLibre."""
        if not v or not v.startswith('MLA'):
            raise ValueError(f"meli_id inválido: {v}")
        return v

    @validator('moneda')
    def validate_moneda(cls, v):
        """Valida que la moneda sea válida."""
        valid_monedas = ['ARS', 'USD']
        if v not in valid_monedas:
            raise ValueError(f"moneda debe ser una de {valid_monedas}")
        return v

    @validator('condicion')
    def validate_condicion(cls, v):
        """Valida que la condición sea válida."""
        valid_condiciones = ['new', 'used']
        if v not in valid_condiciones:
            raise ValueError(f"condicion debe ser una de {valid_condiciones}")
        return v

    @validator('precio')
    def validate_precio_realista(cls, v, values):
        """Valida que el precio sea realista."""
        moneda = values.get('moneda', 'ARS')

        if moneda == 'ARS':
            # Precios en ARS: entre 1M y 100M (2024)
            if v < 1_000_000 or v > 100_000_000:
                logger.warning(f"Precio en ARS fuera de rango típico: ${v:,.0f}")

        elif moneda == 'USD':
            # Precios en USD: entre 5k y 500k
            if v < 5_000 or v > 500_000:
                logger.warning(f"Precio en USD fuera de rango típico: ${v:,.0f}")

        return v

    @validator('kilometros')
    def validate_kilometros(cls, v, values):
        """Valida que los kilómetros sean realistas."""
        if v is not None:
            if v > 1_000_000:
                logger.warning(f"Kilómetros muy altos: {v:,} km")

            # Si es usado, debería tener km > 0
            condicion = values.get('condicion')
            if condicion == 'used' and v == 0:
                logger.warning("Vehículo usado con 0 km")

        return v


def validate_data(data_list: list, validator_class: type[BaseModel]) -> tuple[list, list]:
    """
    Valida una lista de datos contra un validador Pydantic.

    Args:
        data_list: Lista de dicts con datos a validar
        validator_class: Clase validadora Pydantic

    Returns:
        Tuple de (datos_válidos, datos_inválidos)
    """
    valid_data = []
    invalid_data = []

    for i, data in enumerate(data_list):
        try:
            # Validar con Pydantic
            validated = validator_class(**data)
            valid_data.append(validated.model_dump())

        except Exception as e:
            logger.warning(f"Registro {i+1} inválido: {e}")
            invalid_data.append({
                'data': data,
                'error': str(e)
            })

    logger.info(
        f"Validación: {len(valid_data)}/{len(data_list)} registros válidos, "
        f"{len(invalid_data)} inválidos"
    )

    return valid_data, invalid_data
