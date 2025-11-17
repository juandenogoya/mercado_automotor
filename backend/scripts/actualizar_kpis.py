#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear y actualizar KPIs materializados en PostgreSQL

Este script:
- Crea las vistas materializadas de KPIs si no existen
- Actualiza (refresh) las vistas materializadas existentes
- Crea la tabla de features para ML
- Puede ejecutarse manualmente o ser llamado desde otros scripts

Uso:
    # Crear KPIs por primera vez
    python backend/scripts/actualizar_kpis.py --inicializar

    # Actualizar KPIs existentes (después de cargar datos nuevos)
    python backend/scripts/actualizar_kpis.py --refresh

    # Actualizar con modo CONCURRENT (no bloquea lecturas)
    python backend/scripts/actualizar_kpis.py --refresh --concurrent
"""

import sys
import argparse
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime
import time

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings


def crear_engine():
    """Crea la conexión a PostgreSQL"""
    connection_string = settings.get_database_url_sync()
    return create_engine(connection_string)


def ejecutar_sql_file(engine, sql_file_path):
    """
    Ejecuta un archivo SQL completo
    """
    print(f"\n{'='*60}")
    print(f"📄 Ejecutando: {sql_file_path.name}")
    print(f"{'='*60}")

    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        with engine.connect() as conn:
            # Ejecutar el SQL completo
            conn.execute(text(sql_content))
            conn.commit()

        print(f"✅ Archivo ejecutado exitosamente")
        return True

    except Exception as e:
        print(f"❌ Error al ejecutar {sql_file_path.name}: {e}")
        return False


def inicializar_kpis(engine):
    """
    Crea las vistas materializadas y tablas de KPIs por primera vez
    """
    print("\n" + "="*60)
    print("🚀 INICIALIZANDO KPIs MATERIALIZADOS")
    print("="*60)

    sql_file = Path(__file__).parent.parent / "sql" / "crear_kpis_materializados.sql"

    if not sql_file.exists():
        print(f"❌ Error: No se encontró el archivo SQL: {sql_file}")
        return False

    inicio = time.time()

    # Ejecutar el script SQL
    if ejecutar_sql_file(engine, sql_file):
        duracion = time.time() - inicio
        print(f"\n✅ KPIs inicializados exitosamente en {duracion:.2f} segundos")
        print("\n📊 Vistas materializadas creadas:")
        print("   - kpi_segmentacion_demografica")
        print("   - kpi_financiamiento_segmento")
        print("   - kpi_antiguedad_vehiculos")
        print("   - kpi_demanda_activa")
        print("   - ml_features_propension_compra (tabla)")
        print("\n📈 Vista de resumen creada:")
        print("   - v_kpis_resumen_localidad")
        print("\n🔧 Función creada:")
        print("   - refresh_kpis_materializados()")
        return True
    else:
        print("\n❌ Error en la inicialización de KPIs")
        return False


def refresh_kpis(engine, concurrent=True):
    """
    Actualiza las vistas materializadas existentes
    """
    modo = "CONCURRENT" if concurrent else "FULL"

    print("\n" + "="*60)
    print(f"🔄 ACTUALIZANDO KPIs MATERIALIZADOS (modo: {modo})")
    print("="*60)

    inicio = time.time()

    try:
        with engine.connect() as conn:
            # Llamar a la función de refresh
            result = conn.execute(
                text(f"SELECT refresh_kpis_materializados('{modo}')")
            )
            mensaje = result.scalar()
            conn.commit()

        duracion = time.time() - inicio

        print(f"\n{mensaje}")
        print(f"\n✅ KPIs actualizados exitosamente en {duracion:.2f} segundos")

        # Mostrar estadísticas
        mostrar_estadisticas_kpis(engine)

        return True

    except Exception as e:
        print(f"\n❌ Error al actualizar KPIs: {e}")
        return False


def verificar_kpis_existen(engine):
    """
    Verifica si las vistas materializadas ya existen
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM pg_matviews
                WHERE schemaname = 'public'
                AND matviewname LIKE 'kpi_%'
            """))
            count = result.scalar()

        return count > 0

    except:
        return False


def mostrar_estadisticas_kpis(engine):
    """
    Muestra estadísticas sobre los KPIs calculados
    """
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS DE KPIs")
    print("="*60)

    try:
        with engine.connect() as conn:
            # Segmentación demográfica
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT provincia) as provincias,
                    COUNT(DISTINCT localidad) as localidades,
                    COUNT(DISTINCT marca) as marcas,
                    SUM(total_inscripciones) as total_inscripciones
                FROM kpi_segmentacion_demografica
            """))
            row = result.fetchone()

            print(f"\n📈 Segmentación Demográfica:")
            print(f"   - Registros: {row[0]:,}")
            print(f"   - Provincias: {row[1]:,}")
            print(f"   - Localidades: {row[2]:,}")
            print(f"   - Marcas: {row[3]:,}")
            print(f"   - Total Inscripciones: {row[4]:,}")

            # Financiamiento
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total_registros,
                    AVG(indice_financiamiento) as if_promedio
                FROM kpi_financiamiento_segmento
                WHERE indice_financiamiento > 0
            """))
            row = result.fetchone()

            print(f"\n💰 Índice de Financiamiento:")
            print(f"   - Registros: {row[0]:,}")
            print(f"   - IF Promedio: {row[1]:.2f}%")

            # Antigüedad
            result = conn.execute(text("""
                SELECT
                    tipo_transaccion,
                    COUNT(*) as total_registros,
                    AVG(edad_promedio) as edad_prom
                FROM kpi_antiguedad_vehiculos
                GROUP BY tipo_transaccion
            """))
            rows = result.fetchall()

            print(f"\n🚗 Antigüedad de Vehículos:")
            for row in rows:
                print(f"   - {row[0]}: {row[1]:,} registros, edad prom: {row[2]:.1f} años")

            # Demanda activa
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total_registros,
                    AVG(indice_demanda_activa) as ida_promedio
                FROM kpi_demanda_activa
                WHERE indice_demanda_activa > 0
            """))
            row = result.fetchone()

            print(f"\n🔄 Índice de Demanda Activa:")
            print(f"   - Registros: {row[0]:,}")
            print(f"   - IDA Promedio: {row[1]:.2f}%")

            # ML Features
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT provincia) as provincias,
                    COUNT(DISTINCT localidad) as localidades,
                    COUNT(DISTINCT marca) as marcas
                FROM ml_features_propension_compra
            """))
            row = result.fetchone()

            print(f"\n🤖 Features para ML:")
            print(f"   - Registros: {row[0]:,}")
            print(f"   - Provincias: {row[1]:,}")
            print(f"   - Localidades: {row[2]:,}")
            print(f"   - Marcas: {row[3]:,}")

    except Exception as e:
        print(f"\n⚠️ No se pudieron obtener estadísticas: {e}")


def limpiar_kpis(engine):
    """
    Elimina todas las vistas materializadas y tablas de KPIs
    """
    print("\n" + "="*60)
    print("🗑️  LIMPIANDO KPIs MATERIALIZADOS")
    print("="*60)

    try:
        with engine.connect() as conn:
            # Eliminar vistas materializadas
            conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS kpi_segmentacion_demografica CASCADE"))
            conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS kpi_financiamiento_segmento CASCADE"))
            conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS kpi_antiguedad_vehiculos CASCADE"))
            conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS kpi_demanda_activa CASCADE"))

            # Eliminar tabla ML
            conn.execute(text("DROP TABLE IF EXISTS ml_features_propension_compra CASCADE"))

            # Eliminar vista de resumen
            conn.execute(text("DROP VIEW IF EXISTS v_kpis_resumen_localidad CASCADE"))

            # Eliminar función
            conn.execute(text("DROP FUNCTION IF EXISTS refresh_kpis_materializados CASCADE"))

            conn.commit()

        print("✅ KPIs eliminados exitosamente")
        return True

    except Exception as e:
        print(f"❌ Error al limpiar KPIs: {e}")
        return False


def main():
    """
    Función principal
    """
    parser = argparse.ArgumentParser(
        description='Gestión de KPIs materializados en PostgreSQL',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--inicializar',
        action='store_true',
        help='Crear las vistas materializadas por primera vez'
    )

    parser.add_argument(
        '--refresh',
        action='store_true',
        help='Actualizar las vistas materializadas existentes'
    )

    parser.add_argument(
        '--concurrent',
        action='store_true',
        help='Usar modo CONCURRENT para refresh (no bloquea lecturas)'
    )

    parser.add_argument(
        '--limpiar',
        action='store_true',
        help='Eliminar todas las vistas materializadas y tablas de KPIs'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Mostrar solo estadísticas de KPIs existentes'
    )

    args = parser.parse_args()

    # Si no se especifica ninguna acción, mostrar ayuda
    if not any([args.inicializar, args.refresh, args.limpiar, args.stats]):
        parser.print_help()
        return

    # Crear engine
    engine = crear_engine()

    # Extraer información de la URL de base de datos
    db_url = str(settings.database_url)
    # Parsear URL para extraer host y base de datos
    try:
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        db_name = parsed.path.lstrip('/')
        db_host = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
    except:
        db_name = "PostgreSQL"
        db_host = "localhost"

    print("\n" + "="*60)
    print("🚀 GESTOR DE KPIs MATERIALIZADOS - MERCADO AUTOMOTOR")
    print("="*60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Base de datos: {db_name}")
    print(f"🖥️  Host: {db_host}")

    # Ejecutar acciones
    if args.limpiar:
        limpiar_kpis(engine)

    if args.inicializar:
        if verificar_kpis_existen(engine):
            print("\n⚠️ Las vistas materializadas ya existen.")
            respuesta = input("¿Deseas recrearlas? (s/n): ")
            if respuesta.lower() == 's':
                limpiar_kpis(engine)
                inicializar_kpis(engine)
            else:
                print("❌ Operación cancelada")
        else:
            inicializar_kpis(engine)

    if args.refresh:
        if not verificar_kpis_existen(engine):
            print("\n⚠️ Las vistas materializadas no existen.")
            print("💡 Ejecuta con --inicializar primero")
        else:
            refresh_kpis(engine, concurrent=args.concurrent)

    if args.stats:
        if verificar_kpis_existen(engine):
            mostrar_estadisticas_kpis(engine)
        else:
            print("\n⚠️ Las vistas materializadas no existen.")
            print("💡 Ejecuta con --inicializar primero")

    print("\n" + "="*60)
    print("✅ PROCESO COMPLETADO")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
