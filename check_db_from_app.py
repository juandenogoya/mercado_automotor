#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script que usa la misma conexion que funciona en Streamlit
"""

import sys
from pathlib import Path

# Agregar backend al path
sys.path.append(str(Path(__file__).parent))

from backend.config.settings import settings
from sqlalchemy import create_engine, text

def format_bytes(bytes_val):
    """Convertir bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return "{:.2f} {}".format(bytes_val, unit)
        bytes_val /= 1024.0
    return "{:.2f} PB".format(bytes_val)

def main():
    print("Usando la misma configuracion que Streamlit...")
    print()

    try:
        # Usar la misma configuración que app_datos_gob.py
        engine = create_engine(settings.get_database_url_sync())

        with engine.connect() as conn:
            print("=" * 80)
            print("ANALISIS DE BASE DE DATOS")
            print("=" * 80)

            # 1. Tamaño total
            print("\n1. TAMANO TOTAL:")
            print("-" * 80)
            result = conn.execute(text("SELECT pg_database_size(current_database())"))
            total_size = result.fetchone()[0]
            print("   {}".format(format_bytes(total_size)))

            # 2. Por tabla
            print("\n2. TAMANO POR TABLA:")
            print("-" * 80)

            result = conn.execute(text("""
                SELECT
                    tablename,
                    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY size_bytes DESC
            """))

            total_bytes = 0
            for row in result:
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
                    result = conn.execute(text("SELECT COUNT(*) FROM {}".format(table)))
                    count = result.fetchone()[0]
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
            print("\n   OPCIONES DE DEPLOYMENT:")
            print("   " + "-" * 76)

            if total_mb < 500:
                print("\n   [GRATIS] Opcion 1: Supabase")
                print("   - 500 MB PostgreSQL gratis")
                print("   - https://supabase.com")
                print("   - Incluye Auth, Storage, Realtime")
                print("\n   [GRATIS] Opcion 2: Railway")
                print("   - $5 credito inicial gratis")
                print("   - https://railway.app")
            elif total_mb < 1024:
                print("\n   [GRATIS] Opcion 1: Render")
                print("   - 1 GB PostgreSQL gratis")
                print("   - https://render.com")
                print("   - Se duerme tras 15min inactivo")
                print("\n   [GRATIS] Opcion 2: Railway")
                print("   - https://railway.app")
            elif total_mb < 3072:
                print("\n   [GRATIS] Neon")
                print("   - 3 GB PostgreSQL serverless")
                print("   - https://neon.tech")
                print("   - Pausa automatica")
            else:
                print("\n   [!] Base muy grande: {:.1f} GB".format(total_gb))
                print("\n   Opciones:")
                print("   1. FILTRAR DATOS a anos recientes (2023-2025)")
                print("      -> Reducir a ~500MB-1GB")
                print("      -> Deployment GRATIS en Supabase/Render")
                print("\n   2. NGROK (compartir desde local)")
                print("      -> 100% gratis")
                print("      -> Descargar: https://ngrok.com/download")
                print("      -> Ejecutar: ngrok http 8501")
                print("      -> URL temporal para compartir")
                print("\n   3. CLOUD PAGO")
                print("      -> Neon: $19/mes (10 GB)")
                print("      -> Render: $7/mes (10 GB)")

            # 6. Datos por año
            print("\n   DISTRIBUCION POR ANO:")
            print("   " + "-" * 76)

            result = conn.execute(text("""
                SELECT
                    EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                    COUNT(*) as cantidad
                FROM datos_gob_inscripciones
                WHERE tramite_fecha IS NOT NULL
                GROUP BY anio
                ORDER BY anio DESC
                LIMIT 5
            """))

            print("\n   Inscripciones (ultimos 5 anos):")
            for anio, cantidad in result:
                print("      {}: {:>10,d} registros".format(anio, cantidad))

            print("\n" + "=" * 80)
            print("\n   RECOMENDACION:")
            if total_gb > 3:
                print("   -> Usa NGROK para demo inmediata (gratis)")
                print("   -> O filtra a 2023-2025 para deployment permanente gratis")
            elif total_mb < 500:
                print("   -> Supabase + Streamlit Cloud (100% gratis)")
            else:
                print("   -> Neon (3GB) + Streamlit Cloud (gratis)")
            print("=" * 80)

    except Exception as e:
        print("[ERROR]", str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
