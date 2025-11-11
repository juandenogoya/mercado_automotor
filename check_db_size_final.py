#!/usr/bin/env python3
"""
Script para verificar el tamaño de la base de datos PostgreSQL
"""

import psycopg2
import os

def main():
    # Try to get connection details from environment or use defaults
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'mercado_automotor')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')

    # Parse DATABASE_URL if available
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # postgresql://user:password@host:port/database
        try:
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            db_host = parsed.hostname or db_host
            db_port = parsed.port or db_port
            db_name = parsed.path.lstrip('/') or db_name
            db_user = parsed.username or db_user
            db_password = parsed.password or db_password
        except:
            pass

    print(f"Conectando a: {db_user}@{db_host}:{db_port}/{db_name}")
    print()

    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
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
        tables_info = []
        for row in cur.fetchall():
            schema, table, size, size_bytes = row
            total_bytes += size_bytes
            tables_info.append((table, size, size_bytes))
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
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                total_registros += count
                print(f"   {table:40s} {count:>15,d} registros")
            except Exception as e:
                print(f"   {table:40s} (tabla no existe)")

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
            print("      → PostgreSQL + Storage + Auth + Realtime")
            print("      → Muy fácil de configurar")
            print("\n   ✅ ALTERNATIVA: Railway (Free trial: $5 crédito)")
            print("      → https://railway.app")
            print("      → PostgreSQL con 500 MB incluido")
        elif total_mb < 1024:
            print("   ✅ RECOMENDADO: Render (Free tier: 1 GB)")
            print("      → https://render.com")
            print("      → PostgreSQL gratis con 1 GB")
            print("      → Se duerme después de 15 min sin uso")
            print("\n   ✅ ALTERNATIVA: Railway (Free trial)")
            print("      → https://railway.app")
        elif total_mb < 3072:
            print("   ✅ RECOMENDADO: Neon (Free tier: 3 GB)")
            print("      → https://neon.tech")
            print("      → PostgreSQL serverless con 3 GB")
            print("      → Ideal para proyectos medianos")
            print("      → Pausa automática cuando no se usa")
        else:
            print("   ⚠️  Base de datos muy grande para free tiers")
            print("   ")
            print("   OPCIONES:")
            print("   1. Filtrar datos a años recientes (ej: 2023-2025)")
            print("   2. Usar ngrok para compartir temporalmente desde local:")
            print("      → Instalar: snap install ngrok")
            print("      → Registrar cuenta gratis en https://ngrok.com")
            print("      → Ejecutar: ngrok http 8501")
            print("      → Compartir la URL generada")
            print("   3. Usar tier pago:")
            print("      → Neon: $19/mes (10 GB)")
            print("      → Render: $7/mes (PostgreSQL con 10 GB)")
            print("      → Railway: ~$10/mes (uso variable)")

        # 5. Información adicional sobre rango de fechas
        print("\n   ANÁLISIS DE DATOS POR AÑO:")
        print("   " + "-" * 76)

        for table in ['datos_gob_inscripciones', 'datos_gob_transferencias', 'datos_gob_prendas']:
            try:
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
                results = cur.fetchall()
                if results:
                    print(f"\n   {table}:")
                    for row in results:
                        if row[0]:
                            print(f"      {int(row[0])}: {row[1]:>10,d} registros")
            except Exception as e:
                print(f"\n   {table}: (sin datos o tabla no existe)")

        print("\n   💡 CONSEJO: Si la base es muy grande, considera filtrar a años")
        print("      recientes (ej: 2023-2025) para deployment gratuito.")

        print("\n" + "=" * 80)

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"❌ Error de conexión a la base de datos:")
        print(f"   {e}")
        print()
        print("   Verifica que:")
        print("   - PostgreSQL esté corriendo (docker-compose up -d postgres)")
        print("   - Los datos de conexión sean correctos")
        print("   - El firewall permita la conexión")

if __name__ == "__main__":
    main()
