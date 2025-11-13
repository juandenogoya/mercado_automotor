#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para listar todas las tablas disponibles en PostgreSQL.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings

def listar_tablas():
    """Lista todas las tablas en la base de datos."""
    print("\n" + "="*80)
    print("LISTANDO TABLAS EN POSTGRESQL")
    print("="*80)

    try:
        db_url = settings.get_database_url_sync()
        engine = create_engine(db_url)
        print(f"\n✓ Conectado exitosamente")

        # Obtener inspector
        inspector = inspect(engine)

        # Listar schemas
        schemas = inspector.get_schema_names()
        print(f"\n📊 Schemas disponibles: {schemas}")

        # Listar tablas en public schema
        print(f"\n📋 Tablas en schema 'public':")
        tablas = inspector.get_table_names(schema='public')

        if tablas:
            for i, tabla in enumerate(tablas, 1):
                print(f"   {i}. {tabla}")

                # Obtener columnas de la tabla
                columnas = inspector.get_columns(tabla, schema='public')
                print(f"      Columnas ({len(columnas)}):")
                for col in columnas[:10]:  # Primeras 10 columnas
                    print(f"         - {col['name']} ({col['type']})")
                if len(columnas) > 10:
                    print(f"         ... y {len(columnas) - 10} más")
                print()
        else:
            print("   ⚠️  No hay tablas en el schema 'public'")

        engine.dispose()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    listar_tablas()
