"""
FastAPI main application - API REST interna del sistema.
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List, Optional
from loguru import logger

from backend.config.settings import settings
from backend.config.logger import setup_logger
from backend.utils.database import get_db_session, init_db
from backend.models import Patentamiento, Produccion, BCRAIndicador, IndicadorCalculado

# Initialize logger
setup_logger()

# Create FastAPI app
app = FastAPI(
    title="Mercado Automotor API",
    description="API REST para el sistema de inteligencia comercial del mercado automotor argentino",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar origins permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Execute on application startup."""
    logger.info("🚀 Iniciando Mercado Automotor API...")
    logger.info(f"Environment: {settings.environment}")

    # Initialize database
    try:
        init_db()
        logger.success("✓ Base de datos inicializada")
    except Exception as e:
        logger.error(f"✗ Error inicializando base de datos: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown."""
    logger.info("👋 Cerrando Mercado Automotor API...")


# Health check
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Mercado Automotor API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "environment": settings.environment
    }


# ==================== PATENTAMIENTOS ====================

@app.get("/api/patentamientos")
async def get_patentamientos(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    marca: Optional[str] = None,
    tipo_vehiculo: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """
    Obtiene datos de patentamientos.

    Args:
        fecha_desde: Fecha inicial
        fecha_hasta: Fecha final
        marca: Filtrar por marca
        tipo_vehiculo: '0km' o 'usado'
        limit: Límite de resultados
    """
    query = db.query(Patentamiento)

    if fecha_desde:
        query = query.filter(Patentamiento.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Patentamiento.fecha <= fecha_hasta)
    if marca:
        query = query.filter(Patentamiento.marca.ilike(f"%{marca}%"))
    if tipo_vehiculo:
        query = query.filter(Patentamiento.tipo_vehiculo == tipo_vehiculo)

    query = query.order_by(Patentamiento.fecha.desc()).limit(limit)

    results = query.all()

    return {
        "count": len(results),
        "data": [
            {
                "fecha": p.fecha,
                "marca": p.marca,
                "modelo": p.modelo,
                "tipo_vehiculo": p.tipo_vehiculo,
                "cantidad": p.cantidad,
                "fuente": p.fuente
            }
            for p in results
        ]
    }


@app.get("/api/patentamientos/top-marcas")
async def get_top_marcas(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    tipo_vehiculo: str = "0km",
    top_n: int = 10,
    db: Session = Depends(get_db_session)
):
    """
    Obtiene las marcas más patentadas en un período.
    """
    # Si no se especifican fechas, usar último mes
    if not fecha_hasta:
        fecha_hasta = date.today()
    if not fecha_desde:
        fecha_desde = fecha_hasta - timedelta(days=30)

    query = db.query(
        Patentamiento.marca,
        db.func.sum(Patentamiento.cantidad).label('total')
    ).filter(
        Patentamiento.fecha >= fecha_desde,
        Patentamiento.fecha <= fecha_hasta,
        Patentamiento.tipo_vehiculo == tipo_vehiculo
    ).group_by(
        Patentamiento.marca
    ).order_by(
        db.text('total DESC')
    ).limit(top_n)

    results = query.all()

    return {
        "periodo": {
            "desde": fecha_desde,
            "hasta": fecha_hasta
        },
        "tipo_vehiculo": tipo_vehiculo,
        "data": [
            {"marca": r.marca, "total": r.total}
            for r in results
        ]
    }


# ==================== PRODUCCIÓN ====================

@app.get("/api/produccion")
async def get_produccion(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    terminal: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Obtiene datos de producción."""
    query = db.query(Produccion)

    if fecha_desde:
        query = query.filter(Produccion.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Produccion.fecha <= fecha_hasta)
    if terminal:
        query = query.filter(Produccion.terminal.ilike(f"%{terminal}%"))

    query = query.order_by(Produccion.fecha.desc()).limit(limit)

    results = query.all()

    return {
        "count": len(results),
        "data": [
            {
                "fecha": p.fecha,
                "terminal": p.terminal,
                "unidades_producidas": p.unidades_producidas,
                "unidades_exportadas": p.unidades_exportadas
            }
            for p in results
        ]
    }


# ==================== BCRA ====================

@app.get("/api/bcra/indicadores")
async def get_bcra_indicadores(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    indicador: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Obtiene indicadores del BCRA."""
    query = db.query(BCRAIndicador)

    if fecha_desde:
        query = query.filter(BCRAIndicador.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(BCRAIndicador.fecha <= fecha_hasta)
    if indicador:
        query = query.filter(BCRAIndicador.indicador == indicador)

    query = query.order_by(BCRAIndicador.fecha.desc()).limit(limit)

    results = query.all()

    return {
        "count": len(results),
        "data": [
            {
                "fecha": i.fecha,
                "indicador": i.indicador,
                "valor": float(i.valor),
                "unidad": i.unidad
            }
            for i in results
        ]
    }


# ==================== INDICADORES CALCULADOS ====================

@app.get("/api/indicadores")
async def get_indicadores_calculados(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    indicador: Optional[str] = None,
    marca: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Obtiene indicadores calculados."""
    query = db.query(IndicadorCalculado)

    if fecha_desde:
        query = query.filter(IndicadorCalculado.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(IndicadorCalculado.fecha <= fecha_hasta)
    if indicador:
        query = query.filter(IndicadorCalculado.indicador == indicador)
    if marca:
        query = query.filter(IndicadorCalculado.marca.ilike(f"%{marca}%"))

    query = query.order_by(IndicadorCalculado.fecha.desc()).limit(limit)

    results = query.all()

    return {
        "count": len(results),
        "data": [
            {
                "fecha": i.fecha,
                "indicador": i.indicador,
                "marca": i.marca,
                "valor": float(i.valor),
                "detalles": i.detalles
            }
            for i in results
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
