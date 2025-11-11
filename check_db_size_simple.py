#!/usr/bin/env python3
"""
Script para verificar el tamaño de la base de datos PostgreSQL
Versión simplificada usando psycopg2 directamente
"""

import psycopg2
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('/home/user/mercado_automotor/.env')

def main():
    # Conectar a la base de datos
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

    cur = conn.cursor()

    print("=" * 80)
    print("ANÁLISIS DE TAMAÑO DE BASE DE DATOS")
    print("=" * 80)

    # 1. Tamaño total de la base de datos
    print("\n1. TAMAÑO TOTAL DE LA BASE DE DATOS:")
    print("-" * 80)
    cur.execute("""
        SELECT pg_size_pretty(pg_database_size(current_database())) as size
    """)
    row = cur.fetchone()
    print(f"   Tamaño total: {row[0]}")

    # 2. Tamaño por tabla (incluyendo índices)
    print("\n2. TAMAÑO POR TABLA (incluye índices):")
    print("-" * 80)
    cur.execute("""
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """)

    total_bytes = 0
    for row in cur.fetchall():
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
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
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
        print("      → Incluye PostgreSQL + Storage + Auth")
        print("\n   ✅ ALTERNATIVA: Railway (Free tier: 500 MB)")
        print("      → https://railway.app")
        print("      → $5 crédito inicial gratis")
    elif total_mb < 1024:
        print("   ✅ RECOMENDADO: Render (Free tier: 1 GB)")
        print("      → https://render.com")
        print("      → PostgreSQL gratis con 1 GB")
        print("\n   ✅ ALTERNATIVA: Railway (Free trial)")
        print("      → https://railway.app")
    elif total_mb < 3072:
        print("   ✅ RECOMENDADO: Neon (Free tier: 3 GB)")
        print("      → https://neon.tech")
        print("      → PostgreSQL serverless con 3 GB")
        print("      → Ideal para proyectos medianos")
    else:
        print("   ⚠️  Base de datos muy grande para free tiers")
        print("   ")
        print("   OPCIONES:")
        print("   1. Filtrar datos a años recientes (ej: 2023-2025)")
        print("   2. Usar ngrok para compartir temporalmente desde local")
        print("      → ngrok http 8501")
        print("   3. Usar tier pago:")
        print("      → Neon: $19/mes (10 GB)")
        print("      → Render: $7/mes (10 GB)")
        print("      → Railway: ~$10/mes (uso variable)")

    # 5. Información adicional sobre rango de fechas
    print("\n   ANÁLISIS DE DATOS POR AÑO:")
    print("   " + "-" * 76)

    for table in ['datos_gob_inscripciones', 'datos_gob_transferencias', 'datos_gob_prendas']:
        cur.execute(f"""
            SELECT
                EXTRACT(YEAR FROM tramite_fecha) as anio,
                COUNT(*) as cantidad
            FROM {table}
            WHERE tramite_fecha IS NOT NULL
            GROUP BY anio
            ORDER BY anio DESC
            LIMIT 5
        """)
        print(f"\n   {table}:")
        for row in cur.fetchall():
            if row[0]:
                print(f"      {int(row[0])}: {row[1]:>10,d} registros")

    print("\n" + "=" * 80)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
