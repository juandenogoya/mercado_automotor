"""
Explorador de datasets de datos.gob.ar
Busca datasets relacionados con mercado automotor, INDEC, patentamientos

EJECUCIÓN:
python explorar_datasets_gob_ar.py
"""

import requests
import json
from datetime import datetime

print("=" * 80)
print("🔍 EXPLORADOR DE DATASETS - datos.gob.ar")
print("=" * 80)
print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# API base
BASE_URL = "https://datos.gob.ar/api/3"

# Palabras clave para buscar
KEYWORDS = [
    "automotor",
    "patentamiento",
    "vehiculo",
    "indec",
    "automotriz",
    "produccion automotriz",
    "precio automovil",
    "inscripcion vehiculo"
]

print(f"\n🔎 Buscando datasets con palabras clave: {', '.join(KEYWORDS)}")

# Buscar datasets
datasets_encontrados = []

for keyword in KEYWORDS:
    print(f"\n📌 Buscando: '{keyword}'...")

    try:
        url = f"{BASE_URL}/action/package_search"
        params = {
            'q': keyword,
            'rows': 20  # Máximo resultados por búsqueda
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()

            if data.get('success') and data.get('result'):
                count = data['result']['count']
                results = data['result']['results']

                print(f"   ✅ {count} datasets encontrados")

                for dataset in results:
                    dataset_id = dataset.get('id', 'N/A')
                    title = dataset.get('title', 'N/A')
                    org = dataset.get('organization', {}).get('title', 'N/A')

                    # Evitar duplicados
                    if dataset_id not in [d['id'] for d in datasets_encontrados]:
                        datasets_encontrados.append({
                            'id': dataset_id,
                            'title': title,
                            'organization': org,
                            'keyword': keyword
                        })
            else:
                print(f"   ⚠️ Sin resultados")
        else:
            print(f"   ❌ Error {response.status_code}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

# Resumen
print("\n" + "=" * 80)
print(f"📊 RESUMEN: {len(datasets_encontrados)} datasets únicos encontrados")
print("=" * 80)

if datasets_encontrados:
    print("\n📋 DATASETS ENCONTRADOS:\n")

    for idx, dataset in enumerate(datasets_encontrados, 1):
        print(f"{idx}. {dataset['title']}")
        print(f"   ID: {dataset['id']}")
        print(f"   Organización: {dataset['organization']}")
        print(f"   Keyword: {dataset['keyword']}")
        print()

    # Guardar resultados
    output_file = "datasets_encontrados.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(datasets_encontrados, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Resultados guardados en: {output_file}")

    # Datasets más relevantes
    print("\n" + "=" * 80)
    print("🎯 DATASETS MÁS RELEVANTES PARA EXPLORAR:")
    print("=" * 80)

    # Filtrar los más relevantes
    relevantes = [d for d in datasets_encontrados if
                  'patentamiento' in d['title'].lower() or
                  'automotor' in d['title'].lower() or
                  'automotriz' in d['title'].lower() or
                  'vehículo' in d['title'].lower()]

    if relevantes:
        print("\n📌 Para obtener detalles de un dataset, ejecuta:")
        print("   python explorar_dataset_detalle.py --id <dataset_id>\n")

        for idx, dataset in enumerate(relevantes, 1):
            print(f"{idx}. {dataset['title']}")
            print(f"   Comando: python explorar_dataset_detalle.py --id {dataset['id']}")
            print()
    else:
        print("\n⚠️ No se encontraron datasets directamente relevantes")
        print("   Explora manualmente en: https://datos.gob.ar/dataset")

else:
    print("\n⚠️ No se encontraron datasets")
    print("💡 Intenta buscar manualmente en: https://datos.gob.ar")

print("\n" + "=" * 80)
print("✅ EXPLORACIÓN COMPLETADA")
print("=" * 80)
