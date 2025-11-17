#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar qué años de datos están disponibles
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings


def analizar_años():
    """Muestra estadísticas por año de todas las tablas"""

    engine = create_engine(settings.get_database_url_sync())

    print("\n" + "="*80)
    print("📅 ANÁLISIS DE AÑOS DISPONIBLES")
    print("="*80)

    tablas = ['datos_gob_inscripciones', 'datos_gob_transferencias', 'datos_gob_prendas']

    for tabla in tablas:
        print(f"\n📊 {tabla.upper()}")
        print("-" * 80)

        query = text(f"""
            SELECT
                EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
                COUNT(*) as total_registros,
                MIN(tramite_fecha) as fecha_minima,
                MAX(tramite_fecha) as fecha_maxima,
                COUNT(DISTINCT automotor_marca_descripcion) as marcas_distintas,
                COUNT(DISTINCT titular_domicilio_provincia) as provincias_distintas
            FROM {tabla}
            WHERE tramite_fecha IS NOT NULL
            GROUP BY anio
            ORDER BY anio;
        """)

        try:
            with engine.connect() as conn:
                df = pd.read_sql(query, conn)

                if df.empty:
                    print("   ⚠️  No hay datos con fechas válidas")
                else:
                    print(f"\n{'Año':<8} {'Registros':<15} {'Desde':<12} {'Hasta':<12} {'Marcas':<10} {'Provincias'}")
                    print("-" * 80)

                    for _, row in df.iterrows():
                        print(f"{row['anio']:<8} {row['total_registros']:>14,} {str(row['fecha_minima']):<12} {str(row['fecha_maxima']):<12} {row['marcas_distintas']:<10} {row['provincias_distintas']}")

                    print(f"\n   TOTAL: {df['total_registros'].sum():,} registros")
                    print(f"   Rango: {df['anio'].min()} - {df['anio'].max()} ({df['anio'].max() - df['anio'].min() + 1} años)")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Resumen consolidado
    print("\n" + "="*80)
    print("📈 RESUMEN CONSOLIDADO")
    print("="*80)

    query_resumen = text("""
        SELECT
            EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
            SUM(CASE WHEN source = 'inscripciones' THEN cnt ELSE 0 END) as inscripciones,
            SUM(CASE WHEN source = 'transferencias' THEN cnt ELSE 0 END) as transferencias,
            SUM(CASE WHEN source = 'prendas' THEN cnt ELSE 0 END) as prendas,
            SUM(cnt) as total
        FROM (
            SELECT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio, 'inscripciones' as source, COUNT(*) as cnt
            FROM datos_gob_inscripciones
            WHERE tramite_fecha IS NOT NULL
            GROUP BY anio

            UNION ALL

            SELECT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio, 'transferencias' as source, COUNT(*) as cnt
            FROM datos_gob_transferencias
            WHERE tramite_fecha IS NOT NULL
            GROUP BY anio

            UNION ALL

            SELECT EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio, 'prendas' as source, COUNT(*) as cnt
            FROM datos_gob_prendas
            WHERE tramite_fecha IS NOT NULL
            GROUP BY anio
        ) combined
        GROUP BY anio
        ORDER BY anio;
    """)

    try:
        with engine.connect() as conn:
            df_resumen = pd.read_sql(query_resumen, conn)

            if not df_resumen.empty:
                print(f"\n{'Año':<8} {'Inscripciones':<15} {'Transferencias':<15} {'Prendas':<15} {'TOTAL':<15}")
                print("-" * 80)

                for _, row in df_resumen.iterrows():
                    print(f"{row['anio']:<8} {row['inscripciones']:>14,} {row['transferencias']:>14,} {row['prendas']:>14,} {row['total']:>14,}")

                print("-" * 80)
                print(f"{'TOTAL':<8} {df_resumen['inscripciones'].sum():>14,} {df_resumen['transferencias'].sum():>14,} {df_resumen['prendas'].sum():>14,} {df_resumen['total'].sum():>14,}")

                print("\n💡 RECOMENDACIÓN PARA ENTRENAMIENTO ML:")
                print("="*80)

                años_disponibles = df_resumen['anio'].tolist()
                total_años = len(años_disponibles)

                if total_años >= 5:
                    print(f"   ✅ Tienes {total_años} años de datos ({años_disponibles[0]}-{años_disponibles[-1]})")
                    print(f"   📊 USAR TODOS los años para entrenar el modelo")
                    print(f"\n   Comando:")
                    print(f"   python backend/ml/preparar_datos_propension.py --anios {','.join(map(str, años_disponibles))} --output data/ml/")
                elif total_años >= 3:
                    print(f"   ✅ Tienes {total_años} años de datos ({años_disponibles[0]}-{años_disponibles[-1]})")
                    print(f"   📊 USAR TODOS los años")
                    print(f"\n   Comando:")
                    print(f"   python backend/ml/preparar_datos_propension.py --anios {','.join(map(str, años_disponibles))} --output data/ml/")
                else:
                    print(f"   ⚠️  Solo tienes {total_años} años de datos")
                    print(f"   📊 Usa todos los disponibles pero considera que más datos mejorarían el modelo")
                    print(f"\n   Comando:")
                    print(f"   python backend/ml/preparar_datos_propension.py --anios {','.join(map(str, años_disponibles))} --output data/ml/")

    except Exception as e:
        print(f"   ❌ Error en resumen: {e}")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    analizar_años()
