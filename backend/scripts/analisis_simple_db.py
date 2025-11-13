"""
Script simple para analizar la base de datos sin dependencias externas.
Solo usa psycopg2 que ya debe estar instalado.
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Intentar importar psycopg2
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 no está instalado")
    sys.exit(1)

# Obtener DATABASE_URL del archivo .env o usar valor por defecto
try:
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')
except:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/mercado_automotor"

def get_table_stats():
    """Obtiene estadísticas de todas las tablas."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    tablas = [
        'patentamientos',
        'produccion',
        'bcra_indicadores',
        'mercadolibre_listings',
        'ipc',
        'ipc_diario',
        'badlar',
        'tipo_cambio'
    ]

    print("="*80)
    print("ANÁLISIS DE DATASETS - MERCADO AUTOMOTOR")
    print("="*80)
    print()

    for tabla in tablas:
        print(f"📊 {tabla.upper().replace('_', ' ')}")
        print("-" * 80)

        try:
            # Contar registros
            cur.execute(f"SELECT COUNT(*) as count FROM {tabla}")
            count = cur.fetchone()['count']

            if count > 0:
                # Obtener fechas min/max
                cur.execute(f"""
                    SELECT
                        MIN(fecha) as min_fecha,
                        MAX(fecha) as max_fecha
                    FROM {tabla}
                """)
                fechas = cur.fetchone()

                dias = (fechas['max_fecha'] - fechas['min_fecha']).days + 1
                freq = "Diaria" if count/dias > 0.8 else "Mensual" if count/dias < 0.05 else f"~{count/dias:.1f} reg/día"

                print(f"  Registros: {count:,}")
                print(f"  Período: {fechas['min_fecha']} a {fechas['max_fecha']}")
                print(f"  Días cubiertos: {dias:,}")
                print(f"  Frecuencia estimada: {freq}")

                # Estadísticas específicas por tabla
                if tabla == 'ipc_diario':
                    cur.execute(f"""
                        SELECT
                            MIN(ipc_mensual) as min_ipc,
                            MAX(ipc_mensual) as max_ipc,
                            AVG(ipc_mensual) as avg_ipc
                        FROM {tabla}
                    """)
                    stats = cur.fetchone()
                    print(f"  IPC mín: {float(stats['min_ipc']):.2f}%")
                    print(f"  IPC máx: {float(stats['max_ipc']):.2f}%")
                    print(f"  IPC promedio: {float(stats['avg_ipc']):.2f}%")

                elif tabla == 'badlar':
                    cur.execute(f"""
                        SELECT
                            MIN(tasa) as min_tasa,
                            MAX(tasa) as max_tasa,
                            AVG(tasa) as avg_tasa
                        FROM {tabla}
                    """)
                    stats = cur.fetchone()
                    print(f"  Tasa mín: {float(stats['min_tasa']):.2f}% TNA")
                    print(f"  Tasa máx: {float(stats['max_tasa']):.2f}% TNA")
                    print(f"  Tasa promedio: {float(stats['avg_tasa']):.2f}% TNA")

                elif tabla == 'tipo_cambio':
                    cur.execute(f"""
                        SELECT
                            MIN(promedio) as min_tc,
                            MAX(promedio) as max_tc,
                            AVG(promedio) as avg_tc
                        FROM {tabla}
                        WHERE promedio IS NOT NULL
                    """)
                    stats = cur.fetchone()
                    if stats['min_tc']:
                        print(f"  TC mín: ${float(stats['min_tc']):.2f}")
                        print(f"  TC máx: ${float(stats['max_tc']):.2f}")
                        print(f"  TC promedio: ${float(stats['avg_tc']):.2f}")

            else:
                print(f"  ⚠️  Sin datos")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        print()

    # Análisis de período común
    print("="*80)
    print("PERÍODO COMÚN PARA ANÁLISIS INTEGRADO")
    print("="*80)
    print()

    try:
        cur.execute("""
            SELECT
                GREATEST(
                    (SELECT MIN(fecha) FROM ipc_diario),
                    (SELECT MIN(fecha) FROM badlar),
                    (SELECT MIN(fecha) FROM tipo_cambio)
                ) as fecha_desde,
                LEAST(
                    (SELECT MAX(fecha) FROM ipc_diario),
                    (SELECT MAX(fecha) FROM badlar),
                    (SELECT MAX(fecha) FROM tipo_cambio)
                ) as fecha_hasta
        """)
        periodo = cur.fetchone()

        if periodo['fecha_desde'] and periodo['fecha_hasta']:
            dias_comunes = (periodo['fecha_hasta'] - periodo['fecha_desde']).days + 1
            print(f"✅ Período común (datos macro): {periodo['fecha_desde']} a {periodo['fecha_hasta']}")
            print(f"✅ Días con datos completos: {dias_comunes:,}")
            print()
        else:
            print("⚠️  No hay período común")
            print()

    except Exception as e:
        print(f"❌ Error calculando período común: {e}")
        print()

    # Indicadores viables
    print("="*80)
    print("INDICADORES VIABLES")
    print("="*80)
    print()

    # Contar registros actuales
    cur.execute("SELECT COUNT(*) FROM ipc_diario")
    ipc_count = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) FROM badlar")
    badlar_count = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) FROM tipo_cambio")
    tc_count = cur.fetchone()['count']

    if ipc_count > 0 and badlar_count > 0 and tc_count > 0:
        print("✅ Índice de Accesibilidad de Compra")
        print("   Combina: IPC + BADLAR + Tipo de Cambio")
        print(f"   Datos: {ipc_count:,} + {badlar_count:,} + {tc_count:,} registros")
        print("   Viabilidad: ALTA")
        print()

        print("✅ Índice de Costo Financiero Real")
        print("   Fórmula: Tasa Real = BADLAR - IPC")
        print(f"   Datos: {badlar_count:,} + {ipc_count:,} registros")
        print("   Viabilidad: ALTA")
        print()

        print("✅ Índice de Tipo de Cambio Real")
        print("   Fórmula: TCR = TC Nominal / IPC Acumulado")
        print(f"   Datos: {tc_count:,} + {ipc_count:,} registros")
        print("   Viabilidad: ALTA")
        print()

    # Modelos de ML
    print("="*80)
    print("MODELOS DE ML PROPUESTOS")
    print("="*80)
    print()

    if ipc_count > 360:
        print("📈 Forecasting de IPC con Prophet/ARIMA")
        print(f"   Objetivo: Predecir inflación 1-3 meses adelante")
        print(f"   Datos: {ipc_count:,} registros diarios (~{ipc_count//30} meses)")
        print("   Próximo paso: Implementar Prophet")
        print()

    if badlar_count > 180:
        print("📈 Forecasting de BADLAR con ARIMA")
        print(f"   Objetivo: Predecir tasas de interés")
        print(f"   Datos: {badlar_count:,} registros diarios (~{badlar_count//30} meses)")
        print("   Próximo paso: Implementar ARIMA")
        print()

    if ipc_count > 0 and badlar_count > 0 and tc_count > 0:
        print("🔗 Análisis de Correlación Macro")
        print("   Objetivo: Identificar relaciones entre variables")
        print("   Método: Matriz de correlaciones + VAR model")
        print("   Próximo paso: Crear análisis exploratorio")
        print()

    print("="*80)
    print("RECOMENDACIONES")
    print("="*80)
    print()
    print("1. ✅ INMEDIATO: Calcular indicadores macro diarios (3 nuevos indicadores)")
    print("2. ✅ CORTO PLAZO: Implementar forecasting de IPC con Prophet")
    print("3. ✅ CORTO PLAZO: Crear análisis de correlaciones macro")
    print("4. ⚠️  MEDIANO PLAZO: Cargar datos de Patentamientos (ACARA)")
    print("5. ⚠️  MEDIANO PLAZO: Cargar datos de Producción (ADEFA)")
    print("6. ⚠️  LARGO PLAZO: Integrar MercadoLibre para precios")
    print()

    cur.close()
    conn.close()

if __name__ == "__main__":
    get_table_stats()
