#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar el tamaño de la base de datos PostgreSQL
Versión compatible con Windows
"""

import psycopg2
import os
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

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
        try:
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            db_host = parsed.hostname or db_host
            db_port = str(parsed.port) if parsed.port else db_port
            db_name = parsed.path.lstrip('/') or db_name
            db_user = parsed.username or db_user
            db_password = parsed.password or db_password
        except:
            pass

    print("Conectando a: {}@{}:{}/{}".format(db_user, db_host, db_port, db_name))
    print()

    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(
            host=db_host,
            port=int(db_port),
            database=db_name,
            user=db_user,
            password=db_password,
            client_encoding='UTF8'
        )

        cur = conn.cursor()

        print("=" * 80)
        print("ANALISIS DE TAMANO DE BASE DE DATOS")
        print("=" * 80)

        # 1. Tamaño total de la base de datos
        print("\n1. TAMANO TOTAL DE LA BASE DE DATOS:")
        print("-" * 80)
        cur.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as size
        """)
        row = cur.fetchone()
        print("   Tamano total: {}".format(row[0]))

        # 2. Tamaño por tabla (incluyendo índices)
        print("\n2. TAMANO POR TABLA (incluye indices):")
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
            print("   {:40s} {:>15s}".format(table, size))

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
                cur.execute("SELECT COUNT(*) FROM {}".format(table))
                count = cur.fetchone()[0]
                total_registros += count
                print("   {:40s} {:>15,d} registros".format(table, count))
            except Exception as e:
                print("   {:40s} (tabla no existe)".format(table))

        print("-" * 80)
        print("   {:40s} {:>15,d} registros".format('TOTAL', total_registros))

        # 4. Resumen y recomendaciones
        print("\n" + "=" * 80)
        print("RESUMEN Y RECOMENDACIONES:")
        print("=" * 80)

        # Convertir bytes a MB
        total_mb = total_bytes / (1024 * 1024)
        total_gb = total_bytes / (1024 * 1024 * 1024)

        print("\n   Tamano total (datos + indices): {:.2f} MB ({:.3f} GB)".format(total_mb, total_gb))
        print("   Total de registros: {:,d}".format(total_registros))

        print("\n   OPCIONES DE DEPLOYMENT:")
        print("   " + "-" * 76)

        if total_mb < 500:
            print("   OK RECOMENDADO: Supabase (Free tier: 500 MB)")
            print("      -> https://supabase.com")
            print("      -> PostgreSQL + Storage + Auth + Realtime")
            print("      -> Muy facil de configurar")
            print("\n   OK ALTERNATIVA: Railway (Free trial: $5 credito)")
            print("      -> https://railway.app")
            print("      -> PostgreSQL con 500 MB incluido")
        elif total_mb < 1024:
            print("   OK RECOMENDADO: Render (Free tier: 1 GB)")
            print("      -> https://render.com")
            print("      -> PostgreSQL gratis con 1 GB")
            print("      -> Se duerme despues de 15 min sin uso")
            print("\n   OK ALTERNATIVA: Railway (Free trial)")
            print("      -> https://railway.app")
        elif total_mb < 3072:
            print("   OK RECOMENDADO: Neon (Free tier: 3 GB)")
            print("      -> https://neon.tech")
            print("      -> PostgreSQL serverless con 3 GB")
            print("      -> Ideal para proyectos medianos")
            print("      -> Pausa automatica cuando no se usa")
        else:
            print("   ! Base de datos muy grande para free tiers")
            print("   ")
            print("   OPCIONES:")
            print("   1. Filtrar datos a anos recientes (ej: 2023-2025)")
            print("   2. Usar ngrok para compartir temporalmente desde local:")
            print("      -> Descargar de: https://ngrok.com/download")
            print("      -> Registrar cuenta gratis en https://ngrok.com")
            print("      -> Ejecutar: ngrok http 8501")
            print("      -> Compartir la URL generada")
            print("   3. Usar tier pago:")
            print("      -> Neon: $19/mes (10 GB)")
            print("      -> Render: $7/mes (PostgreSQL con 10 GB)")
            print("      -> Railway: ~$10/mes (uso variable)")

        # 5. Información adicional sobre rango de fechas
        print("\n   ANALISIS DE DATOS POR ANO:")
        print("   " + "-" * 76)

        for table in ['datos_gob_inscripciones', 'datos_gob_transferencias', 'datos_gob_prendas']:
            try:
                cur.execute("""
                    SELECT
                        EXTRACT(YEAR FROM tramite_fecha) as anio,
                        COUNT(*) as cantidad
                    FROM {}
                    WHERE tramite_fecha IS NOT NULL
                    GROUP BY anio
                    ORDER BY anio DESC
                    LIMIT 5
                """.format(table))
                results = cur.fetchall()
                if results:
                    print("\n   {}:".format(table))
                    for row in results:
                        if row[0]:
                            print("      {}: {:>10,d} registros".format(int(row[0]), row[1]))
            except Exception as e:
                print("\n   {}: (sin datos o tabla no existe)".format(table))

        print("\n   CONSEJO: Si la base es muy grande, considera filtrar a anos")
        print("      recientes (ej: 2023-2025) para deployment gratuito.")

        print("\n" + "=" * 80)

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print("X Error de conexion a la base de datos:")
        print("   {}".format(e))
        print()
        print("   Verifica que:")
        print("   - PostgreSQL este corriendo")
        print("   - Los datos de conexion sean correctos")
        print("   - El firewall permita la conexion")
    except Exception as e:
        print("X Error inesperado:")
        print("   {}".format(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
