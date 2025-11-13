"""
Script para calcular indicadores macroeconómicos derivados.

Indicadores calculados:
1. Tasa Real = BADLAR - IPC (anualizado)
2. Tipo de Cambio Real (TCR) = TC Nominal / IPC Acumulado
3. Índice de Accesibilidad de Compra
4. Volatilidad Macro (desviación estándar móvil)

Uso:
    python backend/scripts/calcular_indicadores_macro.py
    python backend/scripts/calcular_indicadores_macro.py --export-excel indicadores_macro.xlsx
    python backend/scripts/calcular_indicadores_macro.py --fecha-desde 2024-01-01
"""
import sys
import argparse
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from loguru import logger
from backend.config.logger import setup_logger
from backend.utils.database import get_db, init_db
from backend.models.ipc_diario import IPCDiario
from backend.models.badlar import BADLAR
from backend.models.tipo_cambio import TipoCambio
from backend.models.indicadores_calculados import IndicadorCalculado


def obtener_periodo_comun(db, fecha_desde=None):
    """
    Obtiene el período común entre todos los datasets macro.

    Args:
        db: Sesión de base de datos
        fecha_desde: Fecha desde la cual calcular (opcional)

    Returns:
        Tuple (fecha_desde, fecha_hasta)
    """
    logger.info("Identificando período común de datos...")

    # Obtener fechas mín/máx de cada dataset
    ipc_min = db.query(IPCDiario.fecha).order_by(IPCDiario.fecha.asc()).first()
    ipc_max = db.query(IPCDiario.fecha).order_by(IPCDiario.fecha.desc()).first()

    badlar_min = db.query(BADLAR.fecha).order_by(BADLAR.fecha.asc()).first()
    badlar_max = db.query(BADLAR.fecha).order_by(BADLAR.fecha.desc()).first()

    tc_min = db.query(TipoCambio.fecha).order_by(TipoCambio.fecha.asc()).first()
    tc_max = db.query(TipoCambio.fecha).order_by(TipoCambio.fecha.desc()).first()

    if not all([ipc_min, ipc_max, badlar_min, badlar_max, tc_min, tc_max]):
        logger.error("No hay datos suficientes en alguno de los datasets")
        return None, None

    # Período común
    periodo_desde = max(ipc_min[0], badlar_min[0], tc_min[0])
    periodo_hasta = min(ipc_max[0], badlar_max[0], tc_max[0])

    # Si se especifica fecha_desde, usarla
    if fecha_desde:
        periodo_desde = max(periodo_desde, fecha_desde)

    dias = (periodo_hasta - periodo_desde).days + 1

    logger.success(f"✓ Período común: {periodo_desde} a {periodo_hasta} ({dias:,} días)")

    return periodo_desde, periodo_hasta


def cargar_datos_macro(db, fecha_desde, fecha_hasta):
    """
    Carga los 3 datasets macro en memoria como diccionarios indexados por fecha.

    Returns:
        Tuple (dict_ipc, dict_badlar, dict_tc)
    """
    logger.info(f"\nCargando datos desde {fecha_desde} hasta {fecha_hasta}...")

    # IPC Diario
    ipc_records = db.query(IPCDiario).filter(
        IPCDiario.fecha >= fecha_desde,
        IPCDiario.fecha <= fecha_hasta
    ).order_by(IPCDiario.fecha).all()

    dict_ipc = {r.fecha: float(r.ipc_mensual) for r in ipc_records}
    logger.info(f"  - IPC Diario: {len(dict_ipc):,} registros")

    # BADLAR
    badlar_records = db.query(BADLAR).filter(
        BADLAR.fecha >= fecha_desde,
        BADLAR.fecha <= fecha_hasta
    ).order_by(BADLAR.fecha).all()

    dict_badlar = {r.fecha: float(r.tasa) for r in badlar_records}
    logger.info(f"  - BADLAR: {len(dict_badlar):,} registros")

    # Tipo de Cambio
    tc_records = db.query(TipoCambio).filter(
        TipoCambio.fecha >= fecha_desde,
        TipoCambio.fecha <= fecha_hasta
    ).order_by(TipoCambio.fecha).all()

    dict_tc = {r.fecha: float(r.promedio) for r in tc_records if r.promedio}
    logger.info(f"  - Tipo de Cambio: {len(dict_tc):,} registros")

    return dict_ipc, dict_badlar, dict_tc


def forward_fill(data_dict, fecha_desde, fecha_hasta):
    """
    Forward fill para llenar días faltantes (fines de semana, feriados).

    Args:
        data_dict: Diccionario {fecha: valor}
        fecha_desde: Fecha inicio
        fecha_hasta: Fecha fin

    Returns:
        Diccionario completo con todos los días
    """
    result = {}
    current_date = fecha_desde
    last_value = None

    while current_date <= fecha_hasta:
        if current_date in data_dict:
            last_value = data_dict[current_date]
            result[current_date] = last_value
        elif last_value is not None:
            result[current_date] = last_value

        current_date += timedelta(days=1)

    return result


def calcular_ipc_acumulado(dict_ipc, fecha_desde):
    """
    Calcula IPC acumulado (índice base 100 en fecha_desde).

    Formula: IPC_acum[t] = IPC_acum[t-1] * (1 + IPC[t]/100)
    """
    ipc_acumulado = {}
    fechas_ordenadas = sorted(dict_ipc.keys())

    # Encontrar primera fecha >= fecha_desde
    fechas_validas = [f for f in fechas_ordenadas if f >= fecha_desde]

    if not fechas_validas:
        return {}

    # Inicializar en 100
    ipc_acumulado[fechas_validas[0]] = 100.0

    for i in range(1, len(fechas_validas)):
        fecha_actual = fechas_validas[i]
        fecha_anterior = fechas_validas[i-1]

        # IPC mensual se repite todos los días del mes
        # Solo acumular cuando cambia el valor (nuevo mes)
        if dict_ipc[fecha_actual] != dict_ipc.get(fecha_anterior, 0):
            # Nuevo mes, aplicar inflación
            ipc_acumulado[fecha_actual] = ipc_acumulado[fecha_anterior] * (1 + dict_ipc[fecha_actual] / 100)
        else:
            # Mismo mes, mantener acumulado
            ipc_acumulado[fecha_actual] = ipc_acumulado[fecha_anterior]

    return ipc_acumulado


def calcular_desviacion_movil(valores, window=30):
    """
    Calcula desviación estándar móvil.

    Args:
        valores: Lista de (fecha, valor)
        window: Ventana de días

    Returns:
        Diccionario {fecha: desv_std}
    """
    import statistics

    result = {}
    valores_ordenados = sorted(valores, key=lambda x: x[0])

    for i in range(len(valores_ordenados)):
        fecha = valores_ordenados[i][0]

        # Tomar últimos 'window' valores
        start_idx = max(0, i - window + 1)
        ventana = [v[1] for v in valores_ordenados[start_idx:i+1]]

        if len(ventana) >= 2:
            result[fecha] = statistics.stdev(ventana)
        else:
            result[fecha] = 0.0

    return result


def calcular_indicadores(dict_ipc, dict_badlar, dict_tc, fecha_desde, fecha_hasta):
    """
    Calcula los 4 indicadores macro.

    Returns:
        Dict con 4 listas de tuplas (fecha, valor)
    """
    logger.info("\n" + "="*80)
    logger.info("CALCULANDO INDICADORES MACRO")
    logger.info("="*80)

    # Forward fill para tener todos los días
    logger.info("\n1. Rellenando días faltantes (forward fill)...")
    ipc_completo = forward_fill(dict_ipc, fecha_desde, fecha_hasta)
    badlar_completo = forward_fill(dict_badlar, fecha_desde, fecha_hasta)
    tc_completo = forward_fill(dict_tc, fecha_desde, fecha_hasta)

    logger.info(f"  - IPC: {len(ipc_completo):,} días completos")
    logger.info(f"  - BADLAR: {len(badlar_completo):,} días completos")
    logger.info(f"  - TC: {len(tc_completo):,} días completos")

    # Calcular IPC acumulado
    logger.info("\n2. Calculando IPC acumulado...")
    ipc_acum = calcular_ipc_acumulado(ipc_completo, fecha_desde)
    logger.info(f"  - IPC acumulado: {len(ipc_acum):,} registros")

    # Obtener fechas comunes
    fechas_comunes = sorted(set(ipc_completo.keys()) & set(badlar_completo.keys()) & set(tc_completo.keys()) & set(ipc_acum.keys()))
    logger.info(f"\n3. Fechas con datos completos: {len(fechas_comunes):,}")

    # INDICADOR 1: Tasa Real = BADLAR - IPC (anualizado)
    logger.info("\n4. Calculando Tasa Real (BADLAR - IPC)...")
    tasa_real = []
    for fecha in fechas_comunes:
        ipc_mensual = ipc_completo[fecha]
        ipc_anual = ((1 + ipc_mensual/100) ** 12 - 1) * 100  # Convertir mensual a anual
        badlar = badlar_completo[fecha]

        tasa_real_valor = badlar - ipc_anual
        tasa_real.append((fecha, tasa_real_valor))

    logger.success(f"  ✓ Tasa Real: {len(tasa_real):,} registros")

    # INDICADOR 2: Tipo de Cambio Real
    logger.info("\n5. Calculando Tipo de Cambio Real (TCR)...")
    tcr = []
    for fecha in fechas_comunes:
        tc_nominal = tc_completo[fecha]
        ipc_acumulado = ipc_acum[fecha]

        # TCR = TC Nominal / (IPC Acumulado / 100)
        tcr_valor = tc_nominal / (ipc_acumulado / 100)
        tcr.append((fecha, tcr_valor))

    logger.success(f"  ✓ TCR: {len(tcr):,} registros")

    # INDICADOR 3: Índice de Accesibilidad de Compra
    # Formula simplificada: (TCR * Tasa Real) / IPC Acumulado * 100
    logger.info("\n6. Calculando Índice de Accesibilidad de Compra...")
    accesibilidad = []
    for i, fecha in enumerate(fechas_comunes):
        tcr_valor = tcr[i][1]
        tasa_real_valor = tasa_real[i][1]
        ipc_acumulado = ipc_acum[fecha]

        # Índice compuesto (normalizado a 100 en el primer día)
        accesibilidad_valor = (tcr_valor * (100 + tasa_real_valor)) / ipc_acumulado * 100
        accesibilidad.append((fecha, accesibilidad_valor))

    # Normalizar a 100 en el primer día
    if accesibilidad:
        primer_valor = accesibilidad[0][1]
        accesibilidad = [(f, (v / primer_valor) * 100) for f, v in accesibilidad]

    logger.success(f"  ✓ Accesibilidad: {len(accesibilidad):,} registros")

    # INDICADOR 4: Volatilidad Macro (desviación estándar móvil 30 días)
    logger.info("\n7. Calculando Volatilidad Macro (ventana 30 días)...")

    # Calcular volatilidad de cada variable
    ipc_valores = [(f, ipc_completo[f]) for f in fechas_comunes]
    badlar_valores = [(f, badlar_completo[f]) for f in fechas_comunes]
    tc_valores = [(f, tc_completo[f]) for f in fechas_comunes]

    vol_ipc = calcular_desviacion_movil(ipc_valores, window=30)
    vol_badlar = calcular_desviacion_movil(badlar_valores, window=30)
    vol_tc = calcular_desviacion_movil(tc_valores, window=30)

    # Volatilidad compuesta (promedio normalizado)
    volatilidad = []
    for fecha in fechas_comunes:
        if fecha in vol_ipc and fecha in vol_badlar and fecha in vol_tc:
            # Normalizar cada volatilidad y promediar
            vol_compuesta = (
                vol_ipc[fecha] / (ipc_completo[fecha] + 0.01) * 100 +
                vol_badlar[fecha] / (badlar_completo[fecha] + 0.01) * 100 +
                vol_tc[fecha] / (tc_completo[fecha] + 0.01) * 100
            ) / 3

            volatilidad.append((fecha, vol_compuesta))

    logger.success(f"  ✓ Volatilidad: {len(volatilidad):,} registros")

    logger.info("\n" + "="*80)
    logger.success("✅ INDICADORES CALCULADOS")
    logger.info("="*80)

    return {
        'tasa_real': tasa_real,
        'tcr': tcr,
        'accesibilidad': accesibilidad,
        'volatilidad': volatilidad
    }


def guardar_indicadores(db, indicadores, limpiar_anteriores=False):
    """
    Guarda los indicadores en la tabla indicadores_calculados.

    Args:
        db: Sesión de base de datos
        indicadores: Dict con los 4 indicadores
        limpiar_anteriores: Si True, elimina indicadores anteriores
    """
    logger.info("\n" + "="*80)
    logger.info("GUARDANDO EN POSTGRESQL")
    logger.info("="*80)

    # Limpiar indicadores anteriores si se solicita
    if limpiar_anteriores:
        logger.warning("\nEliminando indicadores anteriores...")
        db.query(IndicadorCalculado).filter(
            IndicadorCalculado.indicador.in_([
                'tasa_real',
                'tipo_cambio_real',
                'accesibilidad_compra',
                'volatilidad_macro'
            ])
        ).delete(synchronize_session=False)
        db.commit()

    # Mapeo de nombres
    nombre_indicadores = {
        'tasa_real': ('tasa_real', 'Tasa de Interés Real (BADLAR - IPC)', '% anual'),
        'tcr': ('tipo_cambio_real', 'Tipo de Cambio Real', 'ARS/USD ajustado'),
        'accesibilidad': ('accesibilidad_compra', 'Índice de Accesibilidad de Compra', 'índice base 100'),
        'volatilidad': ('volatilidad_macro', 'Volatilidad Macro Compuesta', '% normalizado')
    }

    total_guardados = 0

    for key, (nombre_db, descripcion, unidad) in nombre_indicadores.items():
        logger.info(f"\n💾 Guardando {descripcion}...")

        registros = indicadores[key]
        guardados = 0

        for fecha, valor in registros:
            try:
                # Verificar si ya existe
                existing = db.query(IndicadorCalculado).filter(
                    IndicadorCalculado.indicador == nombre_db,
                    IndicadorCalculado.fecha == fecha
                ).first()

                if existing:
                    # Actualizar
                    existing.valor = Decimal(str(round(valor, 4)))
                    existing.descripcion = descripcion
                    existing.unidad = unidad
                else:
                    # Crear nuevo
                    indicador = IndicadorCalculado(
                        fecha=fecha,
                        periodo=fecha.strftime('%Y-%m'),
                        indicador=nombre_db,
                        valor=Decimal(str(round(valor, 4))),
                        descripcion=descripcion,
                        unidad=unidad
                    )
                    db.add(indicador)
                    guardados += 1

            except Exception as e:
                logger.warning(f"  Error en {fecha}: {e}")
                continue

        db.commit()
        logger.success(f"  ✓ {guardados} nuevos registros guardados")
        total_guardados += guardados

    logger.info("\n" + "="*80)
    logger.success(f"✅ TOTAL: {total_guardados} nuevos registros guardados")
    logger.info("="*80)

    return total_guardados


def exportar_a_excel(indicadores, dict_ipc, dict_badlar, dict_tc, filename):
    """
    Exporta los indicadores a Excel con formato.

    Args:
        indicadores: Dict con los 4 indicadores
        dict_ipc, dict_badlar, dict_tc: Datos originales
        filename: Nombre del archivo Excel
    """
    logger.info(f"\n📊 Exportando a Excel: {filename}")

    try:
        import pandas as pd
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment

        # Crear writer
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:

            # HOJA 1: Resumen
            logger.info("  - Creando hoja: Resumen")
            resumen_data = []

            for key, registros in indicadores.items():
                if registros:
                    valores = [v for _, v in registros]
                    resumen_data.append({
                        'Indicador': key.replace('_', ' ').title(),
                        'Registros': len(registros),
                        'Desde': registros[0][0].strftime('%Y-%m-%d'),
                        'Hasta': registros[-1][0].strftime('%Y-%m-%d'),
                        'Mínimo': f"{min(valores):.2f}",
                        'Máximo': f"{max(valores):.2f}",
                        'Promedio': f"{sum(valores)/len(valores):.2f}",
                        'Último': f"{valores[-1]:.2f}"
                    })

            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)

            # HOJA 2: Tasa Real
            logger.info("  - Creando hoja: Tasa Real")
            df_tasa_real = pd.DataFrame([
                {
                    'Fecha': f.strftime('%Y-%m-%d'),
                    'Tasa Real (%)': round(v, 2),
                    'BADLAR (%)': round(dict_badlar.get(f, 0), 2),
                    'IPC Mensual (%)': round(dict_ipc.get(f, 0), 2)
                }
                for f, v in indicadores['tasa_real']
            ])
            df_tasa_real.to_excel(writer, sheet_name='Tasa Real', index=False)

            # HOJA 3: Tipo de Cambio Real
            logger.info("  - Creando hoja: TCR")
            df_tcr = pd.DataFrame([
                {
                    'Fecha': f.strftime('%Y-%m-%d'),
                    'TCR': round(v, 2),
                    'TC Nominal': round(dict_tc.get(f, 0), 2),
                    'IPC Mensual (%)': round(dict_ipc.get(f, 0), 2)
                }
                for f, v in indicadores['tcr']
            ])
            df_tcr.to_excel(writer, sheet_name='TCR', index=False)

            # HOJA 4: Accesibilidad de Compra
            logger.info("  - Creando hoja: Accesibilidad")
            df_accesibilidad = pd.DataFrame([
                {
                    'Fecha': f.strftime('%Y-%m-%d'),
                    'Índice Accesibilidad': round(v, 2)
                }
                for f, v in indicadores['accesibilidad']
            ])
            df_accesibilidad.to_excel(writer, sheet_name='Accesibilidad', index=False)

            # HOJA 5: Volatilidad Macro
            logger.info("  - Creando hoja: Volatilidad")
            df_volatilidad = pd.DataFrame([
                {
                    'Fecha': f.strftime('%Y-%m-%d'),
                    'Volatilidad (%)': round(v, 2)
                }
                for f, v in indicadores['volatilidad']
            ])
            df_volatilidad.to_excel(writer, sheet_name='Volatilidad', index=False)

        logger.success(f"✅ Excel creado exitosamente: {filename}")
        logger.info(f"  Hojas: Resumen, Tasa Real, TCR, Accesibilidad, Volatilidad")

    except ImportError:
        logger.error("❌ pandas y openpyxl son requeridos para exportar a Excel")
    except Exception as e:
        logger.error(f"❌ Error creando Excel: {e}")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Calcular indicadores macroeconómicos derivados",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--export-excel',
        type=str,
        help='Nombre del archivo Excel a exportar (ej: indicadores_macro.xlsx)'
    )

    parser.add_argument(
        '--fecha-desde',
        type=str,
        help='Fecha desde la cual calcular (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--limpiar',
        action='store_true',
        help='Limpiar indicadores anteriores antes de guardar'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logger()

    logger.info("="*80)
    logger.info("🧮 CÁLCULO DE INDICADORES MACROECONÓMICOS")
    logger.info("="*80)

    # Inicializar BD (crear tabla si no existe)
    logger.info("\nInicializando base de datos...")
    init_db()

    # Procesar fecha_desde si se especificó
    fecha_desde_arg = None
    if args.fecha_desde:
        from datetime import datetime
        try:
            fecha_desde_arg = datetime.strptime(args.fecha_desde, '%Y-%m-%d').date()
            logger.info(f"Calculando desde: {fecha_desde_arg}")
        except ValueError:
            logger.error(f"Formato de fecha inválido: {args.fecha_desde}")
            sys.exit(1)

    with get_db() as db:
        # 1. Obtener período común
        fecha_desde, fecha_hasta = obtener_periodo_comun(db, fecha_desde_arg)

        if not fecha_desde or not fecha_hasta:
            logger.error("No se pudo determinar el período común")
            sys.exit(1)

        # 2. Cargar datos
        dict_ipc, dict_badlar, dict_tc = cargar_datos_macro(db, fecha_desde, fecha_hasta)

        # 3. Calcular indicadores
        indicadores = calcular_indicadores(dict_ipc, dict_badlar, dict_tc, fecha_desde, fecha_hasta)

        # 4. Guardar en PostgreSQL
        total_guardados = guardar_indicadores(db, indicadores, limpiar_anteriores=args.limpiar)

    # 5. Exportar a Excel si se especificó
    if args.export_excel:
        exportar_a_excel(indicadores, dict_ipc, dict_badlar, dict_tc, args.export_excel)
    else:
        logger.info("\n💡 Para exportar a Excel: python backend/scripts/calcular_indicadores_macro.py --export-excel indicadores_macro.xlsx")

    logger.info("\n" + "="*80)
    logger.success("✅ PROCESO COMPLETADO")
    logger.info("="*80)
    logger.info(f"  - Indicadores calculados: 4")
    logger.info(f"  - Registros guardados: {total_guardados}")
    logger.info(f"  - Período: {fecha_desde} a {fecha_hasta}")
    logger.info("="*80)


if __name__ == "__main__":
    main()
