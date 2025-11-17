#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para mostrar las columnas de las tablas datos_gob_*
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings


def mostrar_columnas():
    """Muestra las columnas de todas las tablas datos_gob_*"""

    engine = create_engine(settings.get_database_url_sync())

    print("\n" + "="*80)
    print("📋 COLUMNAS DE TABLAS datos_gob_*")
    print("="*80)

    query = text("""
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_name LIKE 'datos_gob_%'
        ORDER BY table_name, ordinal_position;
    """)

    try:
        with engine.connect() as conn:
            resultado = conn.execute(query)
            columnas = resultado.fetchall()

            if not columnas:
                print("\n❌ No se encontraron tablas datos_gob_*")
            else:
                tabla_actual = None
                for col in columnas:
                    if tabla_actual != col[0]:
                        if tabla_actual is not None:
                            print()
                        tabla_actual = col[0]
                        print(f"\n📊 {tabla_actual}")
                        print("-" * 80)
                    print(f"   {col[1]:<50} {col[2]}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    mostrar_columnas()
