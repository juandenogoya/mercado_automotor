#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar tamaño de BD con configuracion de variables de entorno
"""

import psycopg2
import sys
import os

# IMPORTANTE: Configurar variables de entorno ANTES de importar psycopg2
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

def format_bytes(bytes_val):
    """Convertir bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return "{:.2f} {}".format(bytes_val, unit)
        bytes_val /= 1024.0
    return "{:.2f} PB".format(bytes_val)

def main():
    print("Conectando a PostgreSQL...")
    print()

    try:
        # Usar connection string en lugar de parámetros separados
        conn_string = "host=localhost port=5432 dbname=mercado_automotor user=postgres password=postgres client_encoding=UTF8"

        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        print("=" * 80)
        print("ANALISIS DE BASE DE DATOS")
        print("=" * 80)

        # 1. Tamaño total
        print("\n1. TAMANO TOTAL:")
        print("-" * 80)
        cur.execute("SELECT pg_database_size(current_database())")
        total_size = cur.fetchone()[0]
        print("   {}".format(format_bytes(total_size)))

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
        print("\n3. REGISTROS:")
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
                pass

        print("-" * 80)
        print("   {:40s} {:>15,d}".format('TOTAL', total_registros))

        # 4. Resumen
        print("\n" + "=" * 80)
        print("RESUMEN:")
        print("=" * 80)

        total_mb = total_bytes / (1024 * 1024)
        total_gb = total_bytes / (1024 * 1024 * 1024)

        print("\n   Tamano: {:.2f} MB = {:.3f} GB".format(total_mb, total_gb))
        print("   Registros: {:,d}".format(total_registros))

        # 5. Recomendaciones
        print("\n   DEPLOYMENT:")
        print("   " + "-" * 76)

        if total_mb < 500:
            print("   [OK] Supabase (500 MB free)")
            print("   [OK] Railway (500 MB free trial)")
        elif total_mb < 1024:
            print("   [OK] Render (1 GB free)")
        elif total_mb < 3072:
            print("   [OK] Neon (3 GB free)")
        else:
            print("   [!] Base grande: {:.1f} GB".format(total_gb))
            print("")
            print("   OPCIONES:")
            print("   1. Filtrar a anos recientes -> deployment gratis")
            print("   2. ngrok (gratis, compartir local)")
            print("   3. Tier pago: Neon $19/mes, Render $7/mes")

        # 6. Años
        print("\n   DATOS POR ANO (ultimos 5):")
        print("   " + "-" * 76)

        for table in ['datos_gob_inscripciones']:
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
                    print("\n   Inscripciones:")
                    for anio, cantidad in results:
                        print("      {}: {:>10,d} registros".format(anio, cantidad))
            except:
                pass

        print("\n" + "=" * 80)

        cur.close()
        conn.close()

    except Exception as e:
        print("[ERROR]", str(e))

if __name__ == "__main__":
    main()
