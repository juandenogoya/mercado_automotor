"""Script para verificar si existen tablas con datos diarios de indicadores macro."""
from sqlalchemy import create_engine, inspect, text
import sys
from pathlib import Path

sys.path.append('.')
from backend.config.settings import settings

engine = create_engine(settings.get_database_url_sync())
inspector = inspect(engine)

print('\n=== BUSCANDO TABLAS CON DATOS DIARIOS ===\n')

# Buscar tablas que puedan contener datos diarios
tablas_todas = inspector.get_table_names()

# Filtrar tablas relacionadas con IPC, BADLAR, TC
tablas_relevantes = [t for t in tablas_todas if any(keyword in t.lower() for keyword in ['ipc', 'badlar', 'tc', 'cambio', 'indicador', 'macro'])]

print(f"Tablas encontradas relacionadas con indicadores macro:\n")
for tabla in tablas_relevantes:
    print(f"  📊 {tabla}")

    # Contar registros
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
        count = result.fetchone()[0]
        print(f"      Registros: {count:,}")

    # Mostrar primeras columnas
    columnas = inspector.get_columns(tabla)
    print(f"      Columnas: {', '.join([c['name'] for c in columnas[:8]])}")

    # Si tiene columna fecha, mostrar rango
    col_nombres = [c['name'] for c in columnas]
    if 'fecha' in col_nombres:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT MIN(fecha), MAX(fecha) FROM {tabla}"))
            min_f, max_f = result.fetchone()
            print(f"      Rango fechas: {min_f} → {max_f}")

    print()

# Verificar si existe archivo Excel
import os
if os.path.exists('indicadores_macro_corregido.xlsx'):
    print("\n✅ Archivo 'indicadores_macro_corregido.xlsx' EXISTE")

    # Leer Excel para ver estructura
    import pandas as pd
    excel_file = pd.ExcelFile('indicadores_macro_corregido.xlsx')
    print(f"\nHojas en el Excel: {excel_file.sheet_names}")

    for sheet in excel_file.sheet_names:
        df = pd.read_excel('indicadores_macro_corregido.xlsx', sheet_name=sheet, nrows=5)
        print(f"\n  Hoja: {sheet}")
        print(f"  Columnas: {list(df.columns)}")
        print(f"  Primeras filas:")
        print(df.head())
else:
    print("\n⚠️ Archivo 'indicadores_macro_corregido.xlsx' NO EXISTE en directorio actual")

engine.dispose()
