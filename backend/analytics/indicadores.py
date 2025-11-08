"""
Cálculo de indicadores estratégicos del mercado automotor.

Este módulo implementa los 4 indicadores clave:
1. Índice de Tensión de Demanda
2. Rotación Estimada por Terminal
3. Índice de Accesibilidad de Compra
4. Ranking de Atención de Marca
"""
from datetime import date, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from loguru import logger

from backend.models import (
    Patentamiento,
    Produccion,
    BCRAIndicador,
    MercadoLibreListing,
    IndicadorCalculado
)
from backend.utils.database import get_db


def calcular_tension_demanda(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date,
    marcas: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Calcula el Índice de Tensión de Demanda.

    Combina:
    - Patentamientos (ACARA): Tendencia de ventas
    - Tasas de interés (BCRA): Costo de financiamiento
    - Variación de listados ML: Interés del mercado

    Fórmula:
    ITD = (Δ% Patentamientos * 0.5) - (Δ% Tasa BADLAR * 0.3) + (Δ% Listados ML * 0.2)

    Interpretación:
    - ITD > 0: Demanda en crecimiento
    - ITD < 0: Demanda en contracción
    - |ITD| > 20: Cambio significativo

    Args:
        db: Sesión de base de datos
        fecha_desde: Fecha inicial del período
        fecha_hasta: Fecha final del período
        marcas: Lista de marcas a analizar (None = todas)

    Returns:
        Lista de diccionarios con indicadores por marca
    """
    logger.info(f"Calculando Índice de Tensión de Demanda: {fecha_desde} a {fecha_hasta}")

    resultados = []

    # Período anterior para comparación (mismo rango de días, retrocedido)
    dias_periodo = (fecha_hasta - fecha_desde).days
    fecha_desde_anterior = fecha_desde - timedelta(days=dias_periodo)
    fecha_hasta_anterior = fecha_desde - timedelta(days=1)

    # 1. Obtener patentamientos 0km
    query_pat_actual = db.query(Patentamiento).filter(
        Patentamiento.fecha >= fecha_desde,
        Patentamiento.fecha <= fecha_hasta,
        Patentamiento.tipo_vehiculo == '0km'
    )

    query_pat_anterior = db.query(Patentamiento).filter(
        Patentamiento.fecha >= fecha_desde_anterior,
        Patentamiento.fecha <= fecha_hasta_anterior,
        Patentamiento.tipo_vehiculo == '0km'
    )

    if marcas:
        query_pat_actual = query_pat_actual.filter(Patentamiento.marca.in_(marcas))
        query_pat_anterior = query_pat_anterior.filter(Patentamiento.marca.in_(marcas))

    # Agrupar por marca
    df_pat_actual = pd.read_sql(query_pat_actual.statement, db.bind)
    df_pat_anterior = pd.read_sql(query_pat_anterior.statement, db.bind)

    if df_pat_actual.empty:
        logger.warning("No hay datos de patentamientos para el período")
        return []

    # Sumar por marca
    pat_actual = df_pat_actual.groupby('marca')['cantidad'].sum()
    pat_anterior = df_pat_anterior.groupby('marca')['cantidad'].sum()

    # 2. Obtener tasa BADLAR promedio
    query_badlar_actual = db.query(BCRAIndicador).filter(
        BCRAIndicador.fecha >= fecha_desde,
        BCRAIndicador.fecha <= fecha_hasta,
        BCRAIndicador.indicador == 'BADLAR'
    )

    query_badlar_anterior = db.query(BCRAIndicador).filter(
        BCRAIndicador.fecha >= fecha_desde_anterior,
        BCRAIndicador.fecha <= fecha_hasta_anterior,
        BCRAIndicador.indicador == 'BADLAR'
    )

    df_badlar_actual = pd.read_sql(query_badlar_actual.statement, db.bind)
    df_badlar_anterior = pd.read_sql(query_badlar_anterior.statement, db.bind)

    badlar_actual = df_badlar_actual['valor'].mean() if not df_badlar_actual.empty else None
    badlar_anterior = df_badlar_anterior['valor'].mean() if not df_badlar_anterior.empty else None

    # 3. Calcular variaciones
    for marca in pat_actual.index:
        cantidad_actual = pat_actual.get(marca, 0)
        cantidad_anterior = pat_anterior.get(marca, 0)

        # Variación % de patentamientos
        if cantidad_anterior > 0:
            var_patentamientos = ((cantidad_actual - cantidad_anterior) / cantidad_anterior) * 100
        else:
            var_patentamientos = 0 if cantidad_actual == 0 else 100

        # Variación % de tasa BADLAR
        var_badlar = 0
        if badlar_actual and badlar_anterior and badlar_anterior > 0:
            var_badlar = ((badlar_actual - badlar_anterior) / badlar_anterior) * 100

        # Por ahora, sin datos de ML históricos, asumimos 0
        var_listados_ml = 0

        # Calcular ITD
        itd = (var_patentamientos * 0.5) - (var_badlar * 0.3) + (var_listados_ml * 0.2)

        # Interpretación
        if itd > 20:
            interpretacion = "Crecimiento fuerte"
        elif itd > 10:
            interpretacion = "Crecimiento moderado"
        elif itd > -10:
            interpretacion = "Estable"
        elif itd > -20:
            interpretacion = "Contracción moderada"
        else:
            interpretacion = "Contracción fuerte"

        resultados.append({
            'fecha': fecha_hasta,
            'indicador': 'tension_demanda',
            'marca': marca,
            'valor': round(itd, 2),
            'detalles': {
                'var_patentamientos_pct': round(var_patentamientos, 2),
                'var_badlar_pct': round(var_badlar, 2),
                'var_listados_ml_pct': round(var_listados_ml, 2),
                'patentamientos_actual': int(cantidad_actual),
                'patentamientos_anterior': int(cantidad_anterior),
                'interpretacion': interpretacion
            }
        })

    logger.success(f"✓ Calculados {len(resultados)} índices de tensión de demanda")
    return resultados


def calcular_rotacion_stock(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date,
    marcas: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Calcula la Rotación Estimada de Stock por Terminal.

    Fórmula:
    Días de Stock = (Producción Mensual - Exportaciones) / (Patentamientos Diarios Promedio)

    Interpretación:
    - < 30 días: Stock bajo, posible desabastecimiento
    - 30-60 días: Stock saludable
    - 60-90 días: Stock alto, posible sobrestock
    - > 90 días: Sobrestock crítico

    NOTA: Dado que ADEFA solo publica totales por terminal (no por marca desde 2015),
    este indicador calcula a nivel terminal y distribuye proporcionalmente a marcas
    según su participación en patentamientos.

    Args:
        db: Sesión de base de datos
        fecha_desde: Fecha inicial del período
        fecha_hasta: Fecha final del período
        marcas: Lista de marcas a analizar (None = todas)

    Returns:
        Lista de diccionarios con indicadores por terminal/marca
    """
    logger.info(f"Calculando Rotación de Stock: {fecha_desde} a {fecha_hasta}")

    resultados = []

    # 1. Obtener producción por terminal
    query_prod = db.query(Produccion).filter(
        Produccion.fecha >= fecha_desde,
        Produccion.fecha <= fecha_hasta
    )

    df_prod = pd.read_sql(query_prod.statement, db.bind)

    if df_prod.empty:
        logger.warning("No hay datos de producción para el período")
        return []

    # Sumar por terminal
    prod_por_terminal = df_prod.groupby('terminal').agg({
        'unidades_producidas': 'sum',
        'unidades_exportadas': 'sum'
    })

    # 2. Obtener patentamientos 0km
    query_pat = db.query(Patentamiento).filter(
        Patentamiento.fecha >= fecha_desde,
        Patentamiento.fecha <= fecha_hasta,
        Patentamiento.tipo_vehiculo == '0km'
    )

    if marcas:
        query_pat = query_pat.filter(Patentamiento.marca.in_(marcas))

    df_pat = pd.read_sql(query_pat.statement, db.bind)

    if df_pat.empty:
        logger.warning("No hay datos de patentamientos para el período")
        return []

    # Patentamientos totales por marca
    pat_por_marca = df_pat.groupby('marca')['cantidad'].sum()

    # Patentamientos diarios promedio
    dias_periodo = (fecha_hasta - fecha_desde).days + 1
    pat_diarios = pat_por_marca / dias_periodo

    # 3. Calcular rotación por terminal
    # Mapeo marca -> terminal (simplificado, debe ajustarse según realidad)
    mapeo_marca_terminal = {
        'Toyota': 'Toyota',
        'Ford': 'Ford',
        'Volkswagen': 'Volkswagen',
        'Fiat': 'Fiat',
        'Renault': 'Renault',
        'Chevrolet': 'General Motors',
        'Peugeot': 'Peugeot-Citroën',
        'Citroën': 'Peugeot-Citroën',
        'Nissan': 'Nissan',
        'Honda': 'Honda',
    }

    for marca, pat_diario in pat_diarios.items():
        terminal = mapeo_marca_terminal.get(marca, marca)

        if terminal in prod_por_terminal.index:
            produccion = prod_por_terminal.loc[terminal, 'unidades_producidas']
            exportadas = prod_por_terminal.loc[terminal, 'unidades_exportadas']

            # Stock disponible para mercado local
            stock_disponible = produccion - exportadas

            # Días de stock
            if pat_diario > 0:
                dias_stock = stock_disponible / pat_diario
            else:
                dias_stock = float('inf')

            # Interpretación
            if dias_stock < 30:
                interpretacion = "Stock bajo"
                alerta = "warning"
            elif dias_stock <= 60:
                interpretacion = "Stock saludable"
                alerta = "ok"
            elif dias_stock <= 90:
                interpretacion = "Stock alto"
                alerta = "warning"
            else:
                interpretacion = "Sobrestock crítico"
                alerta = "critical"

            resultados.append({
                'fecha': fecha_hasta,
                'indicador': 'rotacion_stock',
                'marca': marca,
                'valor': round(dias_stock, 1),
                'detalles': {
                    'terminal': terminal,
                    'produccion_mensual': int(produccion),
                    'exportaciones_mensual': int(exportadas),
                    'stock_disponible': int(stock_disponible),
                    'patentamientos_diarios': round(pat_diario, 1),
                    'interpretacion': interpretacion,
                    'alerta': alerta
                }
            })

    logger.success(f"✓ Calculados {len(resultados)} índices de rotación de stock")
    return resultados


def calcular_accesibilidad_compra(
    db: Session,
    fecha: date,
    salario_promedio: Optional[float] = None,  # Si None, se obtiene del INDEC
    marcas: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Calcula el Índice de Accesibilidad de Compra.

    Fórmula:
    IAC = (Salario Promedio * Cuotas Financiamiento) / Precio Promedio Vehículo

    Interpretación:
    - IAC > 1.5: Alta accesibilidad
    - IAC 1.0-1.5: Accesibilidad moderada
    - IAC 0.5-1.0: Baja accesibilidad
    - IAC < 0.5: Muy baja accesibilidad

    Args:
        db: Sesión de base de datos
        fecha: Fecha del snapshot de MercadoLibre
        salario_promedio: Salario promedio mensual en ARS (None = obtener de INDEC)
        marcas: Lista de marcas a analizar (None = todas)

    Returns:
        Lista de diccionarios con indicadores por marca
    """
    logger.info(f"Calculando Índice de Accesibilidad de Compra para {fecha}")

    # Obtener salario promedio del INDEC si no se especificó
    if salario_promedio is None:
        try:
            from backend.api_clients import INDECClient
            indec_client = INDECClient()
            salario_promedio = indec_client.get_salario_promedio()

            if salario_promedio is None:
                logger.warning("No se pudo obtener salario de INDEC, usando valor por defecto")
                salario_promedio = 1_000_000.0  # Fallback
            else:
                logger.info(f"✓ Salario INDEC obtenido: ${salario_promedio:,.0f}")

        except Exception as e:
            logger.warning(f"Error obteniendo salario de INDEC: {e}, usando valor por defecto")
            salario_promedio = 1_000_000.0

    resultados = []

    # 1. Obtener precios de MercadoLibre
    query_ml = db.query(MercadoLibreListing).filter(
        MercadoLibreListing.fecha_snapshot == fecha,
        MercadoLibreListing.condicion == 'new'  # Solo 0km
    )

    if marcas:
        query_ml = query_ml.filter(MercadoLibreListing.marca.in_(marcas))

    df_ml = pd.read_sql(query_ml.statement, db.bind)

    if df_ml.empty:
        logger.warning(f"No hay datos de MercadoLibre para {fecha}")
        return []

    # Convertir USD a ARS si es necesario (simplificado)
    # En producción, obtener tipo de cambio del BCRA
    df_ml_ars = df_ml[df_ml['moneda'] == 'ARS'].copy()

    if df_ml_ars.empty:
        logger.warning("No hay listados en ARS")
        return []

    # Precio promedio por marca
    precios_por_marca = df_ml_ars.groupby('marca')['precio'].mean()

    # 2. Obtener tasa de interés promedio (para cálculo de cuotas)
    query_tasa = db.query(BCRAIndicador).filter(
        BCRAIndicador.fecha <= fecha,
        BCRAIndicador.indicador == 'tasa_pf'
    ).order_by(BCRAIndicador.fecha.desc()).limit(1)

    tasa_anual = None
    df_tasa = pd.read_sql(query_tasa.statement, db.bind)

    if not df_tasa.empty:
        tasa_anual = df_tasa['valor'].iloc[0]
    else:
        # Fallback: asumir tasa del 50% anual
        tasa_anual = 50.0
        logger.warning(f"No hay datos de tasa, asumiendo {tasa_anual}% anual")

    # Calcular cuota mensual (sistema francés, 48 meses)
    plazo_meses = 48
    tasa_mensual = tasa_anual / 12 / 100

    # 3. Calcular IAC por marca
    for marca, precio_promedio in precios_por_marca.items():
        # Fórmula de cuota (sistema francés)
        if tasa_mensual > 0:
            factor = (tasa_mensual * (1 + tasa_mensual) ** plazo_meses) / \
                     ((1 + tasa_mensual) ** plazo_meses - 1)
            cuota_mensual = precio_promedio * factor
        else:
            cuota_mensual = precio_promedio / plazo_meses

        # Índice de accesibilidad
        iac = salario_promedio / cuota_mensual if cuota_mensual > 0 else 0

        # Interpretación
        if iac > 1.5:
            interpretacion = "Alta accesibilidad"
            color = "green"
        elif iac >= 1.0:
            interpretacion = "Accesibilidad moderada"
            color = "yellow"
        elif iac >= 0.5:
            interpretacion = "Baja accesibilidad"
            color = "orange"
        else:
            interpretacion = "Muy baja accesibilidad"
            color = "red"

        # Porcentaje del salario que representa la cuota
        pct_salario = (cuota_mensual / salario_promedio * 100) if salario_promedio > 0 else 0

        resultados.append({
            'fecha': fecha,
            'indicador': 'accesibilidad_compra',
            'marca': marca,
            'valor': round(iac, 2),
            'detalles': {
                'precio_promedio': round(precio_promedio, 2),
                'cuota_mensual': round(cuota_mensual, 2),
                'salario_promedio': salario_promedio,
                'plazo_meses': plazo_meses,
                'tasa_anual_pct': round(tasa_anual, 2),
                'pct_salario': round(pct_salario, 1),
                'interpretacion': interpretacion,
                'color': color
            }
        })

    logger.success(f"✓ Calculados {len(resultados)} índices de accesibilidad")
    return resultados


def calcular_ranking_atencion(
    db: Session,
    fecha: date,
    top_n: int = 20
) -> List[Dict[str, Any]]:
    """
    Calcula el Ranking de Atención de Marca.

    Combina:
    - Cantidad de listados activos en MercadoLibre
    - Variación de listados vs período anterior
    - Patentamientos recientes

    Fórmula:
    Score = (Listados ML * 0.4) + (Δ% Listados * 0.3) + (Patentamientos * 0.3)

    Args:
        db: Sesión de base de datos
        fecha: Fecha del análisis
        top_n: Número de marcas a retornar en el ranking

    Returns:
        Lista de diccionarios con ranking ordenado
    """
    logger.info(f"Calculando Ranking de Atención para {fecha}")

    # 1. Listados de MercadoLibre
    query_ml = db.query(MercadoLibreListing).filter(
        MercadoLibreListing.fecha_snapshot == fecha
    )

    df_ml = pd.read_sql(query_ml.statement, db.bind)

    if df_ml.empty:
        logger.warning(f"No hay datos de MercadoLibre para {fecha}")
        return []

    listados_por_marca = df_ml.groupby('marca').size()

    # 2. Patentamientos últimos 30 días
    fecha_desde_pat = fecha - timedelta(days=30)

    query_pat = db.query(Patentamiento).filter(
        Patentamiento.fecha >= fecha_desde_pat,
        Patentamiento.fecha <= fecha,
        Patentamiento.tipo_vehiculo == '0km'
    )

    df_pat = pd.read_sql(query_pat.statement, db.bind)

    pat_por_marca = df_pat.groupby('marca')['cantidad'].sum() if not df_pat.empty else pd.Series()

    # 3. Calcular score
    marcas_todas = set(listados_por_marca.index) | set(pat_por_marca.index)

    resultados = []

    for marca in marcas_todas:
        listados = listados_por_marca.get(marca, 0)
        patentamientos = pat_por_marca.get(marca, 0)

        # Score combinado (normalizado)
        # Normalización simple: dividir por percentil 90
        norm_listados = listados / listados_por_marca.quantile(0.9) if len(listados_por_marca) > 0 else 0
        norm_pat = patentamientos / pat_por_marca.quantile(0.9) if len(pat_por_marca) > 0 else 0

        score = (norm_listados * 0.5) + (norm_pat * 0.5)

        resultados.append({
            'fecha': fecha,
            'indicador': 'ranking_atencion',
            'marca': marca,
            'valor': round(score * 100, 2),  # Score en escala 0-100
            'detalles': {
                'listados_ml': int(listados),
                'patentamientos_30d': int(patentamientos),
                'score_raw': round(score, 3)
            }
        })

    # Ordenar por score descendente
    resultados.sort(key=lambda x: x['valor'], reverse=True)

    # Agregar posición en ranking
    for i, resultado in enumerate(resultados[:top_n], start=1):
        resultado['detalles']['ranking_posicion'] = i

        if i <= 5:
            resultado['detalles']['categoria'] = 'Top 5'
        elif i <= 10:
            resultado['detalles']['categoria'] = 'Top 10'
        else:
            resultado['detalles']['categoria'] = 'Top 20'

    logger.success(f"✓ Calculado ranking de {len(resultados[:top_n])} marcas")
    return resultados[:top_n]


def guardar_indicadores(db: Session, indicadores: List[Dict[str, Any]]) -> int:
    """
    Guarda indicadores calculados en la base de datos.

    Args:
        db: Sesión de base de datos
        indicadores: Lista de indicadores a guardar

    Returns:
        Número de indicadores guardados
    """
    if not indicadores:
        return 0

    saved_count = 0

    for indicador in indicadores:
        try:
            # Verificar si ya existe
            existing = db.query(IndicadorCalculado).filter(
                IndicadorCalculado.fecha == indicador['fecha'],
                IndicadorCalculado.indicador == indicador['indicador'],
                IndicadorCalculado.marca == indicador.get('marca')
            ).first()

            if not existing:
                nuevo_indicador = IndicadorCalculado(**indicador)
                db.add(nuevo_indicador)
                saved_count += 1
            else:
                # Actualizar valor
                existing.valor = indicador['valor']
                existing.detalles = indicador.get('detalles')

        except Exception as e:
            logger.error(f"Error guardando indicador: {e}")
            continue

    db.commit()
    logger.info(f"✓ Guardados {saved_count} indicadores en BD")

    return saved_count
