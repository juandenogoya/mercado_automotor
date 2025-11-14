#!/usr/bin/env python3
"""Script temporal para explorar estructura de datos transaccionales."""

import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect, text

sys.path.append(str(Path(__file__).parent))
from backend.config.settings import settings

def explorar_datasets():
    """Explora estructura de datasets transaccionales y macro."""

    engine = create_engine(settings.get_database_url_sync())
    inspector = inspect(engine)

    # Datasets a explorar
    datasets_transaccionales = [
        'datos_gob_inscripciones',
        'datos_gob_transferencias',
        'datos_gob_prendas'
    ]

    datasets_macro = ['ipc', 'badlar', 'tipo_cambio', 'indicadores_calculados']

    print("=" * 80)
    print("EXPLORACIÓN DE DATASETS TRANSACCIONALES")
    print("=" * 80)

    for tabla in datasets_transaccionales:
        try:
            if tabla in inspector.get_table_names():
                print(f"\n📊 {tabla.upper()}")
                print("-" * 80)

                # Columnas
                columnas = inspector.get_columns(tabla)
                print(f"Total columnas: {len(columnas)}\n")

                for col in columnas:
                    print(f"  - {col['name']:<40} {str(col['type']):<20} {'NULL' if col['nullable'] else 'NOT NULL'}")

                # Conteo de registros
                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
                    count = result.fetchone()[0]
                    print(f"\nRegistros totales: {count:,}")

                    # Muestra de datos únicos en columnas clave
                    if 'automotor_marca_descripcion' in [c['name'] for c in columnas]:
                        result = conn.execute(text(f"""
                            SELECT COUNT(DISTINCT automotor_marca_descripcion) as marcas,
                                   COUNT(DISTINCT automotor_modelo_descripcion) as modelos,
                                   COUNT(DISTINCT registro_seccional_provincia) as provincias,
                                   COUNT(DISTINCT titular_genero) as generos
                            FROM {tabla}
                        """))
                        stats = result.fetchone()
                        print(f"\nEstadísticas:")
                        print(f"  - Marcas únicas: {stats[0]}")
                        print(f"  - Modelos únicos: {stats[1]}")
                        print(f"  - Provincias únicas: {stats[2]}")
                        print(f"  - Géneros únicos: {stats[3]}")
        except Exception as e:
            print(f"Error en {tabla}: {e}")

    print("\n" + "=" * 80)
    print("EXPLORACIÓN DE DATASETS MACRO")
    print("=" * 80)

    for tabla in datasets_macro:
        try:
            if tabla in inspector.get_table_names():
                print(f"\n📈 {tabla.upper()}")
                print("-" * 80)

                columnas = inspector.get_columns(tabla)
                print(f"Total columnas: {len(columnas)}\n")

                for col in columnas:
                    print(f"  - {col['name']:<40} {str(col['type']):<20}")

                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
                    count = result.fetchone()[0]

                    # Rango de fechas
                    fecha_col = 'fecha' if tabla != 'ipc' else 'indice_tiempo'
                    result = conn.execute(text(f"SELECT MIN({fecha_col}), MAX({fecha_col}) FROM {tabla}"))
                    min_fecha, max_fecha = result.fetchone()

                    print(f"\nRegistros: {count:,}")
                    print(f"Rango: {min_fecha} → {max_fecha}")
        except Exception as e:
            print(f"Error en {tabla}: {e}")

    engine.dispose()

if __name__ == "__main__":
    explorar_datasets()
