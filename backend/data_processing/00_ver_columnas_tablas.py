#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script rápido para ver qué columnas existen en cada tabla.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text, inspect

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings

def main():
    print("="*80)
    print("COLUMNAS DE LAS TABLAS")
    print("="*80)

    # Conectar
    engine = create_engine(settings.get_database_url_sync())
    inspector = inspect(engine)

    tablas = ['datos_gob_inscripciones', 'datos_gob_transferencias', 'datos_gob_prendas']

    for tabla in tablas:
        print(f"\n{'='*80}")
        print(f"TABLA: {tabla}")
        print('='*80)

        columnas = inspector.get_columns(tabla)

        print(f"\nTotal columnas: {len(columnas)}\n")

        for i, col in enumerate(columnas, 1):
            print(f"{i:2}. {col['name']:40} ({col['type']})")

    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()
