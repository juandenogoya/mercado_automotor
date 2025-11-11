#!/usr/bin/env python3
"""
Script para verificar el tamaño de la base de datos PostgreSQL
"""

import sys
sys.path.append('/home/user/mercado_automotor')

from backend.config.settings import get_db_connection
from sqlalchemy import text

def main():
    # Obtener conexión
    engine = get_db_connection()

    with engine.connect() as conn:
        print("=" * 80)
        print("ANÁLISIS DE TAMAÑO DE BASE DE DATOS")
        print("=" * 80)

        # 1. Tamaño total de la base de datos
        print("\n1. TAMAÑO TOTAL DE LA BASE DE DATOS:")
        print("-" * 80)
        query_total = text("""
            SELECT
                pg_size_pretty(pg_database_size(current_database())) as size
        """)
        result = conn.execute(query_total)
        row = result.fetchone()
        print(f"   Tamaño total: {row[0]}")

        # 2. Tamaño por tabla (incluyendo índices)
        print("\n2. TAMAÑO POR TABLA (incluye índices):")
        print("-" * 80)
        query_tables = text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)
        result = conn.execute(query_tables)
        total_bytes = 0
        for row in result:
            schema, table, size, size_bytes = row
            total_bytes += size_bytes
            print(f"   {table:40s} {size:>15s}")

        # 3. Cantidad de registros por tabla
        print("\n3. CANTIDAD DE REGISTROS POR TABLA:")
        print("-" * 80)

        tables = [
            'datos_gob_inscripciones',
            'datos_gob_transferencias',
            'datos_gob_prendas',
            'datos_gob_registros_seccionales'
        ]

        total_registros = 0
        for table in tables:
            query_count = text(f"SELECT COUNT(*) FROM {table}")
            result = conn.execute(query_count)
            count = result.fetchone()[0]
            total_registros += count
            print(f"   {table:40s} {count:>15,d} registros")

        print("-" * 80)
        print(f"   {'TOTAL':40s} {total_registros:>15,d} registros")

        # 4. Resumen y recomendaciones
        print("\n" + "=" * 80)
        print("RESUMEN Y RECOMENDACIONES:")
        print("=" * 80)

        # Convertir bytes a MB
        total_mb = total_bytes / (1024 * 1024)
        total_gb = total_bytes / (1024 * 1024 * 1024)

        print(f"\n   Tamaño total (datos + índices): {total_mb:.2f} MB ({total_gb:.3f} GB)")
        print(f"   Total de registros: {total_registros:,d}")

        print("\n   OPCIONES DE DEPLOYMENT:")
        print("   " + "-" * 76)

        if total_mb < 500:
            print("   ✅ RECOMENDADO: Supabase (Free tier: 500 MB)")
            print("      → https://supabase.com")
            print("   ✅ ALTERNATIVA: Railway (Free tier: 500 MB)")
            print("      → https://railway.app")
        elif total_mb < 1024:
            print("   ✅ RECOMENDADO: Render (Free tier: 1 GB)")
            print("      → https://render.com")
            print("   ✅ ALTERNATIVA: Railway (Free tier con límite)")
        elif total_mb < 3072:
            print("   ✅ RECOMENDADO: Neon (Free tier: 3 GB)")
            print("      → https://neon.tech")
        else:
            print("   ⚠️  Base de datos muy grande para free tiers")
            print("   ")
            print("   OPCIONES:")
            print("   1. Filtrar datos a años recientes (ej: 2023-2025)")
            print("   2. Usar ngrok para compartir temporalmente desde local")
            print("   3. Usar tier pago (~$5-10/mes)")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
