"""
Análisis exploratorio de todos los datasets disponibles en PostgreSQL.

Este script:
1. Analiza cobertura temporal de cada dataset
2. Identifica gaps y datos faltantes
3. Evalúa correlaciones entre datasets
4. Propone modelos viables con los datos actuales
"""
import sys
from pathlib import Path
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from loguru import logger
from backend.config.logger import setup_logger
from backend.utils.database import get_db
from backend.models.ipc import IPC
from backend.models.ipc_diario import IPCDiario
from backend.models.badlar import BADLAR
from backend.models.tipo_cambio import TipoCambio
from backend.models.patentamientos import Patentamiento
from backend.models.produccion import Produccion
from backend.models.mercadolibre_listings import MercadoLibreListing
from backend.models.bcra_indicadores import BCRAIndicador


def analizar_cobertura_temporal(db):
    """Analiza la cobertura temporal de cada dataset."""
    logger.info("\n" + "="*80)
    logger.info("1. COBERTURA TEMPORAL DE DATASETS")
    logger.info("="*80)

    datasets = {
        'IPC (mensual)': (IPC, IPC.fecha),
        'IPC Diario': (IPCDiario, IPCDiario.fecha),
        'BADLAR': (BADLAR, BADLAR.fecha),
        'Tipo de Cambio': (TipoCambio, TipoCambio.fecha),
        'Patentamientos': (Patentamiento, Patentamiento.fecha),
        'Producción': (Produccion, Produccion.fecha),
        'MercadoLibre': (MercadoLibreListing, MercadoLibreListing.fecha_scraping),
        'BCRA Indicadores': (BCRAIndicador, BCRAIndicador.fecha),
    }

    cobertura = []

    for nombre, (modelo, campo_fecha) in datasets.items():
        try:
            count = db.query(modelo).count()

            if count > 0:
                min_fecha = db.query(campo_fecha).order_by(campo_fecha.asc()).first()[0]
                max_fecha = db.query(campo_fecha).order_by(campo_fecha.desc()).first()[0]

                # Calcular días de cobertura
                dias_cobertura = (max_fecha - min_fecha).days + 1

                # Calcular frecuencia promedio
                freq_dias = dias_cobertura / count if count > 1 else 0

                if freq_dias <= 1.5:
                    frecuencia = "Diaria"
                elif freq_dias <= 7.5:
                    frecuencia = "Semanal"
                elif freq_dias <= 31:
                    frecuencia = "Mensual"
                else:
                    frecuencia = f"~{int(freq_dias)} días"

                cobertura.append({
                    'Dataset': nombre,
                    'Registros': f"{count:,}",
                    'Desde': min_fecha.strftime('%Y-%m-%d'),
                    'Hasta': max_fecha.strftime('%Y-%m-%d'),
                    'Días': f"{dias_cobertura:,}",
                    'Frecuencia': frecuencia
                })
            else:
                cobertura.append({
                    'Dataset': nombre,
                    'Registros': '0',
                    'Desde': '-',
                    'Hasta': '-',
                    'Días': '-',
                    'Frecuencia': '-'
                })
        except Exception as e:
            logger.warning(f"Error analizando {nombre}: {e}")
            cobertura.append({
                'Dataset': nombre,
                'Registros': 'ERROR',
                'Desde': '-',
                'Hasta': '-',
                'Días': '-',
                'Frecuencia': '-'
            })

    # Imprimir tabla manual
    logger.info("\n")
    for item in cobertura:
        logger.info(f"  {item['Dataset']:25s} | {item['Registros']:>10s} | {item['Desde']:12s} - {item['Hasta']:12s} | {item['Días']:>8s} días | {item['Frecuencia']:10s}")

    return cobertura


def analizar_datos_macro(db):
    """Análisis detallado de los datos macroeconómicos."""
    logger.info("\n" + "="*80)
    logger.info("2. ANÁLISIS DETALLADO - DATOS MACROECONÓMICOS")
    logger.info("="*80)

    # IPC Diario
    logger.info("\n📊 IPC DIARIO:")
    ipc_diario = db.query(IPCDiario).order_by(IPCDiario.fecha).all()
    if ipc_diario:
        valores_ipc = [float(r.ipc_mensual) for r in ipc_diario]
        fechas = [r.fecha for r in ipc_diario]
        periodos_vigencia = set([r.periodo_vigencia for r in ipc_diario])

        logger.info(f"  - Registros totales: {len(ipc_diario):,}")
        logger.info(f"  - Período: {min(fechas)} a {max(fechas)}")
        logger.info(f"  - IPC mín: {min(valores_ipc):.2f}%")
        logger.info(f"  - IPC máx: {max(valores_ipc):.2f}%")
        logger.info(f"  - IPC promedio: {sum(valores_ipc)/len(valores_ipc):.2f}%")
        logger.info(f"  - IPC último: {valores_ipc[-1]:.2f}%")
        logger.info(f"  - Meses únicos cubiertos: {len(periodos_vigencia)}")

    # BADLAR
    logger.info("\n📊 BADLAR (Tasa de Interés):")
    badlar = db.query(BADLAR).order_by(BADLAR.fecha).all()
    if badlar:
        tasas = [float(r.tasa) for r in badlar]
        fechas_badlar = [r.fecha for r in badlar]

        logger.info(f"  - Registros totales: {len(badlar):,}")
        logger.info(f"  - Período: {min(fechas_badlar)} a {max(fechas_badlar)}")
        logger.info(f"  - Tasa mín: {min(tasas):.2f}% TNA")
        logger.info(f"  - Tasa máx: {max(tasas):.2f}% TNA")
        logger.info(f"  - Tasa promedio: {sum(tasas)/len(tasas):.2f}% TNA")
        logger.info(f"  - Tasa actual: {tasas[-1]:.2f}% TNA")

    # Tipo de Cambio
    logger.info("\n📊 TIPO DE CAMBIO (USD/ARS):")
    tc = db.query(TipoCambio).order_by(TipoCambio.fecha).all()
    if tc:
        promedios = [float(r.promedio) for r in tc if r.promedio]
        fechas_tc = [r.fecha for r in tc]

        logger.info(f"  - Registros totales: {len(tc):,}")
        logger.info(f"  - Período: {min(fechas_tc)} a {max(fechas_tc)}")
        logger.info(f"  - TC mín: ${min(promedios):.2f}")
        logger.info(f"  - TC máx: ${max(promedios):.2f}")
        logger.info(f"  - TC promedio: ${sum(promedios)/len(promedios):.2f}")
        logger.info(f"  - TC actual: ${promedios[-1]:.2f}")

        # Calcular devaluación
        tc_inicial = promedios[0]
        tc_final = promedios[-1]
        devaluacion = ((tc_final - tc_inicial) / tc_inicial) * 100
        logger.info(f"  - Devaluación total: {devaluacion:.2f}%")


def identificar_periodo_comun(db):
    """Identifica el período común entre todos los datasets macro."""
    logger.info("\n" + "="*80)
    logger.info("3. PERÍODO COMÚN PARA ANÁLISIS INTEGRADO")
    logger.info("="*80)

    # Obtener fechas min/max de cada dataset macro (diario)
    datasets_diarios = {
        'IPC Diario': IPCDiario,
        'BADLAR': BADLAR,
        'Tipo de Cambio': TipoCambio
    }

    fechas_min = []
    fechas_max = []

    for nombre, modelo in datasets_diarios.items():
        count = db.query(modelo).count()
        if count > 0:
            min_f = db.query(modelo.fecha).order_by(modelo.fecha.asc()).first()[0]
            max_f = db.query(modelo.fecha).order_by(modelo.fecha.desc()).first()[0]
            fechas_min.append(min_f)
            fechas_max.append(max_f)
            logger.info(f"  {nombre:20s}: {min_f} a {max_f}")

    if fechas_min and fechas_max:
        periodo_comun_desde = max(fechas_min)
        periodo_comun_hasta = min(fechas_max)
        dias_comunes = (periodo_comun_hasta - periodo_comun_desde).days + 1

        logger.success(f"\n✓ Período común: {periodo_comun_desde} a {periodo_comun_hasta}")
        logger.success(f"✓ Días con datos completos: {dias_comunes:,}")

        return periodo_comun_desde, periodo_comun_hasta, dias_comunes

    return None, None, 0


def evaluar_indicadores_viables(db):
    """Evalúa qué indicadores son viables con los datos actuales."""
    logger.info("\n" + "="*80)
    logger.info("4. INDICADORES VIABLES CON DATOS ACTUALES")
    logger.info("="*80)

    # Contar registros por dataset
    ipc_count = db.query(IPCDiario).count()
    badlar_count = db.query(BADLAR).count()
    tc_count = db.query(TipoCambio).count()
    patent_count = db.query(Patentamiento).count()
    prod_count = db.query(Produccion).count()
    ml_count = db.query(MercadoLibreListing).count()

    indicadores = []

    # 1. Índice de Accesibilidad de Compra
    if ipc_count > 0 and badlar_count > 0 and tc_count > 0:
        indicadores.append({
            'Indicador': '✅ Índice de Accesibilidad de Compra',
            'Datasets': 'IPC + BADLAR + Tipo Cambio',
            'Viabilidad': 'ALTA',
            'Notas': f'{ipc_count:,} + {badlar_count:,} + {tc_count:,} registros diarios'
        })
    else:
        indicadores.append({
            'Indicador': '❌ Índice de Accesibilidad de Compra',
            'Datasets': 'IPC + BADLAR + Tipo Cambio',
            'Viabilidad': 'BAJA',
            'Notas': 'Faltan datos macro'
        })

    # 2. Índice de Tensión de Demanda
    if patent_count > 0 and badlar_count > 0 and ipc_count > 0:
        indicadores.append({
            'Indicador': '✅ Índice de Tensión de Demanda',
            'Datasets': 'Patentamientos + BADLAR + IPC',
            'Viabilidad': 'MEDIA',
            'Notas': f'{patent_count:,} patentamientos + datos macro'
        })
    else:
        indicadores.append({
            'Indicador': '⚠️  Índice de Tensión de Demanda',
            'Datasets': 'Patentamientos + BADLAR + IPC',
            'Viabilidad': 'BAJA',
            'Notas': f'Patentamientos: {patent_count} registros (necesita datos)'
        })

    # 3. Rotación de Stock
    if patent_count > 0 and prod_count > 0:
        indicadores.append({
            'Indicador': '✅ Rotación Estimada por Terminal',
            'Datasets': 'Producción + Patentamientos',
            'Viabilidad': 'MEDIA',
            'Notas': f'{prod_count:,} + {patent_count:,} registros mensuales'
        })
    else:
        indicadores.append({
            'Indicador': '❌ Rotación Estimada por Terminal',
            'Datasets': 'Producción + Patentamientos',
            'Viabilidad': 'BAJA',
            'Notas': f'Producción: {prod_count}, Patentamientos: {patent_count}'
        })

    # 4. Ranking de Atención de Marca
    if ml_count > 0:
        indicadores.append({
            'Indicador': '✅ Ranking de Atención de Marca',
            'Datasets': 'MercadoLibre Listings',
            'Viabilidad': 'MEDIA',
            'Notas': f'{ml_count:,} listings (falta Google Trends)'
        })
    else:
        indicadores.append({
            'Indicador': '❌ Ranking de Atención de Marca',
            'Datasets': 'MercadoLibre + Google Trends',
            'Viabilidad': 'BAJA',
            'Notas': f'MercadoLibre: {ml_count} registros'
        })

    # 5. NUEVO: Índice de Costo de Financiamiento Real
    if badlar_count > 0 and ipc_count > 0:
        indicadores.append({
            'Indicador': '✅ Índice de Costo Financiero Real',
            'Datasets': 'BADLAR - IPC (tasa real)',
            'Viabilidad': 'ALTA',
            'Notas': 'Tasa real = BADLAR - Inflación (indicador nuevo)'
        })

    # 6. NUEVO: Índice de Poder Adquisitivo
    if tc_count > 0 and ipc_count > 0:
        indicadores.append({
            'Indicador': '✅ Índice de Poder Adquisitivo',
            'Datasets': 'Tipo Cambio / IPC acumulado',
            'Viabilidad': 'ALTA',
            'Notas': 'TCR = TC nominal / inflación acumulada'
        })

    # Imprimir indicadores
    logger.info("\n")
    for ind in indicadores:
        logger.info(f"  {ind['Indicador']}")
        logger.info(f"    Datasets: {ind['Datasets']}")
        logger.info(f"    Viabilidad: {ind['Viabilidad']}")
        logger.info(f"    Notas: {ind['Notas']}")
        logger.info("")

    return indicadores


def proponer_modelos(db):
    """Propone modelos de ML viables con los datos actuales."""
    logger.info("\n" + "="*80)
    logger.info("5. MODELOS DE ML/ANÁLISIS PROPUESTOS")
    logger.info("="*80)

    modelos = []

    # Modelo 1: Forecasting de IPC
    ipc_count = db.query(IPCDiario).count()
    if ipc_count > 360:  # ~1 año de datos diarios
        modelos.append({
            'Modelo': '📈 Forecasting IPC (Prophet/ARIMA)',
            'Objetivo': 'Predecir inflación 1-3 meses adelante',
            'Datos requeridos': f'✅ {ipc_count:,} registros diarios',
            'Viabilidad': 'ALTA',
            'Próximo paso': 'Implementar Prophet con IPC diario'
        })

    # Modelo 2: Forecasting BADLAR
    badlar_count = db.query(BADLAR).count()
    if badlar_count > 180:  # ~6 meses
        modelos.append({
            'Modelo': '📈 Forecasting BADLAR (ARIMA)',
            'Objetivo': 'Predecir tasas de interés',
            'Datos requeridos': f'✅ {badlar_count:,} registros diarios',
            'Viabilidad': 'ALTA',
            'Próximo paso': 'Implementar ARIMA con BADLAR'
        })

    # Modelo 3: Análisis de correlación macro
    if ipc_count > 0 and badlar_count > 0:
        modelos.append({
            'Modelo': '🔗 Correlación Macro (IPC vs BADLAR vs TC)',
            'Objetivo': 'Identificar relaciones entre variables macro',
            'Datos requeridos': f'✅ IPC, BADLAR, TC disponibles',
            'Viabilidad': 'ALTA',
            'Próximo paso': 'Crear matriz de correlaciones y análisis VAR'
        })

    # Modelo 4: Detección de anomalías
    if badlar_count > 90:
        modelos.append({
            'Modelo': '🚨 Detección de Anomalías (Isolation Forest)',
            'Objetivo': 'Detectar eventos atípicos en tasas e inflación',
            'Datos requeridos': f'✅ {badlar_count:,} registros',
            'Viabilidad': 'MEDIA',
            'Próximo paso': 'Implementar Isolation Forest sklearn'
        })

    # Modelo 5: Clustering temporal
    periodo_desde, periodo_hasta, dias = identificar_periodo_comun(db)
    if dias > 180:
        modelos.append({
            'Modelo': '🎯 Clustering de Regímenes Macro',
            'Objetivo': 'Identificar períodos de alta/baja inflación',
            'Datos requeridos': f'✅ {dias:,} días con datos completos',
            'Viabilidad': 'MEDIA',
            'Próximo paso': 'K-means con features macro diarias'
        })

    # Imprimir modelos
    logger.info("\n")
    for mod in modelos:
        logger.info(f"  {mod['Modelo']}")
        logger.info(f"    Objetivo: {mod['Objetivo']}")
        logger.info(f"    Datos: {mod['Datos requeridos']}")
        logger.info(f"    Viabilidad: {mod['Viabilidad']}")
        logger.info(f"    Próximo paso: {mod['Próximo paso']}")
        logger.info("")

    return modelos


def main():
    """Función principal."""
    setup_logger()

    logger.info("="*80)
    logger.info("📊 ANÁLISIS EXPLORATORIO DE DATOS - MERCADO AUTOMOTOR")
    logger.info("="*80)

    with get_db() as db:
        # 1. Cobertura temporal
        cobertura = analizar_cobertura_temporal(db)

        # 2. Análisis macro detallado
        analizar_datos_macro(db)

        # 3. Período común
        periodo_desde, periodo_hasta, dias = identificar_periodo_comun(db)

        # 4. Indicadores viables
        indicadores = evaluar_indicadores_viables(db)

        # 5. Modelos propuestos
        modelos = proponer_modelos(db)

    # Resumen final
    logger.info("\n" + "="*80)
    logger.success("✅ ANÁLISIS COMPLETADO")
    logger.info("="*80)

    logger.info("\n📋 RESUMEN:")
    logger.info(f"  - Datasets con datos: {sum(1 for c in cobertura if c['Registros'] != '0' and c['Registros'] != 'ERROR')}/8")
    logger.info(f"  - Indicadores viables: {sum(1 for i in indicadores if '✅' in i['Indicador'])}/{len(indicadores)}")
    logger.info(f"  - Modelos propuestos: {len(modelos)}")

    if periodo_desde and periodo_hasta:
        logger.info(f"  - Período común: {periodo_desde} a {periodo_hasta} ({dias} días)")

    logger.info("\n🎯 RECOMENDACIONES:")
    logger.info("  1. CORTO PLAZO: Implementar indicadores macro (Accesibilidad, Tasa Real)")
    logger.info("  2. CORTO PLAZO: Crear análisis de correlaciones entre IPC, BADLAR, TC")
    logger.info("  3. MEDIANO PLAZO: Forecasting de IPC con Prophet (predecir inflación)")
    logger.info("  4. MEDIANO PLAZO: Cargar datos de Patentamientos y Producción (ACARA/ADEFA)")
    logger.info("  5. LARGO PLAZO: Integrar MercadoLibre para precios de vehículos")

    logger.info("\n" + "="*80)


if __name__ == "__main__":
    main()
