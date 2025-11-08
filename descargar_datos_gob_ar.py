"""
Script para descargar y analizar datos de datos.gob.ar
Descarga CSVs de inscripciones y transferencias de automotores

EJECUCIÓN:
python descargar_datos_gob_ar.py

Dataset: Estadística de trámites de automotores (Ministerio de Justicia)
"""

import requests
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("📥 DESCARGA DE DATOS - datos.gob.ar")
print("=" * 80)
print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Crear directorio para datos descargados
output_dir = Path(__file__).parent / "datos_gob_ar"
output_dir.mkdir(exist_ok=True)

# URLs directas de los CSVs (obtenidas de datos.gob.ar)
# Dataset: Estadística de trámites de automotores (Ministerio de Justicia)
csv_recursos = [
    {
        'name': 'Inscripciones iniciales de automotores 2000-2025',
        'url': 'https://datos.jus.gob.ar/dataset/1ab0cc03-ab9b-4520-975c-5757d87d1061/resource/6cbbad3b-8e11-47f5-8937-e6b1e6262449/download/estadistica-inscripciones-iniciales-automotores-2000-01-2025-09.csv',
        'tipo': 'inscripciones'
    },
    {
        'name': 'Transferencias de automotores 2000-2025',
        'url': 'https://datos.jus.gob.ar/dataset/1ab0cc03-ab9b-4520-975c-5757d87d1061/resource/bde302c5-ca4b-4dd3-91d1-e310cc96034c/download/estadistica-transferencias-automotores-2000-01-2025-09.csv',
        'tipo': 'transferencias'
    }
]

print(f"\n📋 {len(csv_recursos)} archivos CSV encontrados")
print("=" * 80)

# Descargar y analizar cada CSV
dataframes = {}

for idx, recurso in enumerate(csv_recursos, 1):
    nombre = recurso.get('name', 'Sin nombre')
    url = recurso.get('url', '')
    tipo = recurso.get('tipo', f'archivo_{idx}')

    print(f"\n{idx}. {nombre}")
    print(f"   URL: {url}")

    # Descargar
    print(f"   📥 Descargando...")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
        }
        response = requests.get(url, headers=headers, timeout=60)

        if response.status_code == 200:
            # Guardar archivo
            filename = output_dir / f"{tipo}.csv"
            with open(filename, 'wb') as f:
                f.write(response.content)

            print(f"   ✅ Descargado: {filename}")
            print(f"   📏 Tamaño: {len(response.content) / 1024:.1f} KB")

            # Analizar CSV
            print(f"   📊 Analizando estructura...")

            try:
                df = pd.read_csv(filename)
                dataframes[tipo] = df

                print(f"   ✅ CSV parseado correctamente")
                print(f"   📋 Filas: {len(df):,}")
                print(f"   📋 Columnas: {len(df.columns)}")
                print(f"   🔤 Columnas: {list(df.columns)[:5]}{'...' if len(df.columns) > 5 else ''}")

                # Mostrar primeras filas
                print(f"\n   📄 Primeras 3 filas:")
                print("   " + "-" * 76)
                for i, row in df.head(3).iterrows():
                    print(f"   {dict(row)}")

            except Exception as e:
                print(f"   ⚠️ Error parseando CSV: {e}")
                print(f"   💡 Intentando leer primeras líneas...")

                with open(filename, 'r', encoding='utf-8') as f:
                    print(f"   Primeras 5 líneas:")
                    for i, line in enumerate(f):
                        if i >= 5:
                            break
                        print(f"   {line.strip()}")

        else:
            print(f"   ❌ Error HTTP {response.status_code}")

    except Exception as e:
        print(f"   ❌ Error descargando: {e}")

# Resumen final
print("\n" + "=" * 80)
print("📊 RESUMEN DE DESCARGA")
print("=" * 80)

for tipo, df in dataframes.items():
    print(f"\n✅ {tipo.upper()}")
    print(f"   Filas: {len(df):,}")
    print(f"   Columnas: {list(df.columns)}")
    print(f"   Rango de datos:")

    # Intentar detectar columnas de fecha/período
    date_cols = [col for col in df.columns if any(word in col.lower() for word in ['fecha', 'periodo', 'mes', 'año', 'anio'])]
    if date_cols:
        for col in date_cols[:2]:  # Primeras 2 columnas de fecha
            print(f"      {col}: {df[col].min()} a {df[col].max()}")

    # Mostrar info de valores numéricos
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) > 0:
        print(f"   Columnas numéricas: {list(numeric_cols)[:3]}{'...' if len(numeric_cols) > 3 else ''}")

print("\n" + "=" * 80)
print("✅ DESCARGA COMPLETADA")
print("=" * 80)

print(f"\n📁 Archivos guardados en: {output_dir}")
print(f"\n🎯 Próximos pasos:")
print("   1. Revisar estructura de los CSVs")
print("   2. Crear script de carga a PostgreSQL")
print("   3. Actualizar dashboard para mostrar estos datos")
print("=" * 80)
