"""
Script para verificar el estado de carga de chunks de SIOGRANOS
============================================================================
Muestra:
- Chunks completados vs pendientes
- Estadísticas de registros cargados
- Chunks con errores
- Próximos chunks a procesar
============================================================================
"""

import os
from datetime import datetime, timedelta
from typing import List, Tuple
from collections import defaultdict

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

FECHA_INICIO = datetime(2020, 1, 1)
FECHA_FIN = datetime.now()
CHUNK_DAYS = 7

def get_db_connection():
    """Obtiene conexión a PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'mercado_automotor'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        cursor_factory=RealDictCursor
    )


def generar_todos_chunks() -> List[Tuple[datetime, datetime]]:
    """Genera lista de todos los chunks posibles"""
    chunks = []
    current = FECHA_INICIO

    while current < FECHA_FIN:
        chunk_fin = min(current + timedelta(days=CHUNK_DAYS), FECHA_FIN)
        chunks.append((current, chunk_fin))
        current = chunk_fin

    return chunks


def obtener_estado_chunks(conn):
    """Obtiene estado de todos los chunks desde la DB"""
    cursor = conn.cursor()

    sql = """
        SELECT
            fecha_desde,
            fecha_hasta,
            estado,
            registros_procesados,
            registros_insertados,
            registros_duplicados,
            registros_error,
            duracion_segundos,
            fin_ejecucion,
            mensaje_error
        FROM siogranos_etl_control
        ORDER BY fecha_desde
    """

    cursor.execute(sql)
    resultados = cursor.fetchall()
    cursor.close()

    # Crear mapa de chunks completados
    chunks_map = {}
    for row in resultados:
        key = (row['fecha_desde'], row['fecha_hasta'])
        chunks_map[key] = dict(row)

    return chunks_map


def obtener_estadisticas_generales(conn):
    """Obtiene estadísticas generales de la tabla"""
    cursor = conn.cursor()

    sql = """
        SELECT
            COUNT(*) as total_registros,
            COUNT(DISTINCT fecha_operacion) as dias_con_datos,
            MIN(fecha_operacion) as fecha_min,
            MAX(fecha_operacion) as fecha_max,
            COUNT(DISTINCT id_grano) as total_granos,
            COUNT(DISTINCT nombre_provincia_procedencia) as total_provincias,
            SUM(volumen_tn) as volumen_total_tn,
            AVG(precio_tn) as precio_promedio_tn
        FROM siogranos_operaciones
    """

    cursor.execute(sql)
    stats = cursor.fetchone()
    cursor.close()

    return dict(stats) if stats else {}


def main():
    print("\n" + "="*80)
    print("🔍 VERIFICACIÓN DE CHUNKS - SIOGRANOS ETL")
    print("="*80)

    try:
        conn = get_db_connection()
        print("✅ Conectado a PostgreSQL\n")
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return

    try:
        # Generar todos los chunks
        todos_chunks = generar_todos_chunks()
        total_chunks = len(todos_chunks)

        # Obtener estado desde DB
        chunks_map = obtener_estado_chunks(conn)

        # Clasificar chunks
        completados = []
        con_errores = []
        pendientes = []

        for chunk in todos_chunks:
            key = (chunk[0].date(), chunk[1].date())

            if key in chunks_map:
                info = chunks_map[key]
                if info['estado'] == 'completed' and info['registros_error'] == 0:
                    completados.append((chunk, info))
                else:
                    con_errores.append((chunk, info))
            else:
                pendientes.append(chunk)

        # RESUMEN GENERAL
        print("📊 RESUMEN GENERAL")
        print("-"*80)
        print(f"Total de chunks: {total_chunks}")
        print(f"✅ Completados: {len(completados)} ({len(completados)*100//total_chunks if total_chunks > 0 else 0}%)")
        print(f"⏳ Pendientes: {len(pendientes)} ({len(pendientes)*100//total_chunks if total_chunks > 0 else 0}%)")
        print(f"❌ Con errores: {len(con_errores)}")
        print()

        # ESTADÍSTICAS DE DATOS
        stats = obtener_estadisticas_generales(conn)

        if stats and stats.get('total_registros', 0) > 0:
            print("📈 ESTADÍSTICAS DE DATOS CARGADOS")
            print("-"*80)
            print(f"Total registros: {stats['total_registros']:,}")
            print(f"Días con datos: {stats['dias_con_datos']:,}")
            print(f"Fecha mínima: {stats['fecha_min']}")
            print(f"Fecha máxima: {stats['fecha_max']}")
            print(f"Granos diferentes: {stats['total_granos']}")
            print(f"Provincias: {stats['total_provincias']}")

            if stats.get('volumen_total_tn'):
                print(f"Volumen total: {stats['volumen_total_tn']:,.2f} TN")
            if stats.get('precio_promedio_tn'):
                print(f"Precio promedio: ${stats['precio_promedio_tn']:,.2f}/TN")
            print()

        # ÚLTIMOS CHUNKS COMPLETADOS
        if completados:
            print("✅ ÚLTIMOS 10 CHUNKS COMPLETADOS")
            print("-"*80)

            tabla = []
            for chunk, info in completados[-10:]:
                tabla.append([
                    chunk[0].strftime('%Y-%m-%d'),
                    chunk[1].strftime('%Y-%m-%d'),
                    info['registros_insertados'],
                    info['registros_duplicados'],
                    f"{info['duracion_segundos']:.1f}s" if info['duracion_segundos'] else 'N/A'
                ])

            print(tabulate(
                tabla,
                headers=['Desde', 'Hasta', 'Insertados', 'Duplicados', 'Duración'],
                tablefmt='simple'
            ))
            print()

        # CHUNKS CON ERRORES
        if con_errores:
            print("❌ CHUNKS CON ERRORES")
            print("-"*80)

            tabla = []
            for chunk, info in con_errores:
                tabla.append([
                    chunk[0].strftime('%Y-%m-%d'),
                    chunk[1].strftime('%Y-%m-%d'),
                    info['estado'],
                    info['registros_error'],
                    info['mensaje_error'][:40] if info['mensaje_error'] else 'N/A'
                ])

            print(tabulate(
                tabla,
                headers=['Desde', 'Hasta', 'Estado', 'Errores', 'Mensaje'],
                tablefmt='simple'
            ))
            print()

        # PRÓXIMOS CHUNKS PENDIENTES
        if pendientes:
            print("⏳ PRÓXIMOS 15 CHUNKS PENDIENTES")
            print("-"*80)

            tabla = []
            for chunk in pendientes[:15]:
                dias = (chunk[1] - chunk[0]).days
                tabla.append([
                    chunk[0].strftime('%Y-%m-%d'),
                    chunk[1].strftime('%Y-%m-%d'),
                    f"{dias} días"
                ])

            print(tabulate(
                tabla,
                headers=['Desde', 'Hasta', 'Período'],
                tablefmt='simple'
            ))
            print()

            if len(pendientes) > 15:
                print(f"... y {len(pendientes) - 15} chunks más\n")

        # RESUMEN POR AÑO
        print("📅 PROGRESO POR AÑO")
        print("-"*80)

        completados_por_año = defaultdict(int)
        pendientes_por_año = defaultdict(int)

        for chunk, _ in completados:
            año = chunk[0].year
            completados_por_año[año] += 1

        for chunk in pendientes:
            año = chunk[0].year
            pendientes_por_año[año] += 1

        años = sorted(set(list(completados_por_año.keys()) + list(pendientes_por_año.keys())))

        tabla = []
        for año in años:
            comp = completados_por_año[año]
            pend = pendientes_por_año[año]
            total = comp + pend
            porcentaje = (comp * 100 // total) if total > 0 else 0

            tabla.append([
                año,
                comp,
                pend,
                total,
                f"{porcentaje}%"
            ])

        print(tabulate(
            tabla,
            headers=['Año', 'Completados', 'Pendientes', 'Total', '% Completo'],
            tablefmt='simple'
        ))
        print()

        # RECOMENDACIONES
        print("💡 RECOMENDACIONES")
        print("-"*80)

        if len(pendientes) > 0:
            dias_estimados = len(pendientes) * 3 / 86400  # Asumiendo 3s por chunk
            print(f"• Quedan {len(pendientes)} chunks pendientes")
            print(f"• Tiempo estimado: ~{dias_estimados:.1f} horas")
            print(f"• Ejecuta: python etl_siogranos.py")
        elif len(con_errores) > 0:
            print(f"• Hay {len(con_errores)} chunks con errores")
            print(f"• Revisa los logs para diagnosticar problemas")
            print(f"• Vuelve a ejecutar el ETL para reintentar")
        else:
            print("• ✅ ¡Todo está actualizado!")
            print("• Considera configurar una carga incremental diaria")

        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
