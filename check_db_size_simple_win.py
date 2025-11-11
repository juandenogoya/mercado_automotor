#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple para verificar el tamaño de la base de datos PostgreSQL
Version simplificada para Windows
"""

import psycopg2
import sys
import os

def format_bytes(bytes_val):
    """Convertir bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return "{:.2f} {}".format(bytes_val, unit)
        bytes_val /= 1024.0
    return "{:.2f} PB".format(bytes_val)

def main():
    # Configuración de conexión
    conn_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'mercado_automotor',
        'user': 'postgres',
        'password': 'postgres'
    }

    print("Intentando conectar a PostgreSQL...")
    print("Host: {}:{}".format(conn_params['host'], conn_params['port']))
    print("Database: {}".format(conn_params['database']))
    print()

    try:
        # Crear conexión SIN especificar encoding (dejar que use el default)
        conn = psycopg2.connect(**conn_params)
        conn.set_client_encoding('UTF8')

        cur = conn.cursor()

        print("=" * 80)
        print("ANALISIS DE BASE DE DATOS")
        print("=" * 80)

        # 1. Tamaño total
        print("\n1. TAMANO TOTAL:")
        print("-" * 80)
        cur.execute("SELECT pg_database_size(current_database())")
        total_size = cur.fetchone()[0]
        print("   Tamano: {}".format(format_bytes(total_size)))

        # 2. Por tabla
        print("\n2. TAMANO POR TABLA:")
        print("-" * 80)

        cur.execute("""
            SELECT
                tablename,
                pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY size_bytes DESC
        """)

        total_bytes = 0
        for row in cur.fetchall():
            table, size_bytes = row
            total_bytes += size_bytes
            print("   {:40s} {:>15s}".format(table, format_bytes(size_bytes)))

        # 3. Cantidad de registros
        print("\n3. REGISTROS POR TABLA:")
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
                print("   {:40s} {:>15,d}".format(table, count))
            except:
                print("   {:40s} (no existe)".format(table))

        print("-" * 80)
        print("   {:40s} {:>15,d}".format('TOTAL', total_registros))

        # 4. Resumen
        print("\n" + "=" * 80)
        print("RESUMEN:")
        print("=" * 80)

        total_mb = total_bytes / (1024 * 1024)
        total_gb = total_bytes / (1024 * 1024 * 1024)

        print("\n   Tamano total: {:.2f} MB ({:.3f} GB)".format(total_mb, total_gb))
        print("   Total registros: {:,d}".format(total_registros))

        # 5. Recomendaciones
        print("\n   RECOMENDACIONES DE DEPLOYMENT:")
        print("   " + "-" * 76)

        if total_mb < 500:
            print("   [OK] Supabase (Free: 500 MB) - https://supabase.com")
            print("   [OK] Railway (Trial: 500 MB) - https://railway.app")
        elif total_mb < 1024:
            print("   [OK] Render (Free: 1 GB) - https://render.com")
            print("   [OK] Railway (Trial) - https://railway.app")
        elif total_mb < 3072:
            print("   [OK] Neon (Free: 3 GB) - https://neon.tech")
        else:
            print("   [!] Base muy grande para free tiers ({:.1f} GB)".format(total_gb))
            print("")
            print("   OPCIONES:")
            print("   1. Filtrar a 2023-2025 (deployment gratis)")
            print("   2. ngrok para compartir local (gratis)")
            print("      - Descargar: https://ngrok.com/download")
            print("      - Ejecutar: ngrok http 8501")
            print("   3. Tier pago:")
            print("      - Neon: $19/mes (10 GB)")
            print("      - Render: $7/mes (10 GB)")

        # 6. Datos por año
        print("\n   DATOS POR ANO:")
        print("   " + "-" * 76)

        for table in ['datos_gob_inscripciones', 'datos_gob_transferencias', 'datos_gob_prendas']:
            try:
                cur.execute("""
                    SELECT
                        EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
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
                    for anio, cantidad in results:
                        print("      {}: {:>10,d} registros".format(anio, cantidad))
            except:
                pass

        print("\n" + "=" * 80)

        cur.close()
        conn.close()

    except psycopg2.OperationalError as e:
        print("[ERROR] No se pudo conectar a PostgreSQL")
        print("Detalles:", str(e))
        print()
        print("Verifica que:")
        print("- PostgreSQL este corriendo")
        print("- El usuario y password sean correctos")
        print("- El puerto 5432 este disponible")
    except Exception as e:
        print("[ERROR] Error inesperado:", str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
