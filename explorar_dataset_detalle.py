"""
Explorador de detalles de un dataset específico de datos.gob.ar
Muestra recursos, formatos, URLs de descarga

EJECUCIÓN:
python explorar_dataset_detalle.py --id <dataset_id>

Ejemplo:
python explorar_dataset_detalle.py --id justicia-estadistica-tramites-automotores
"""

import requests
import json
import argparse
from datetime import datetime

print("=" * 80)
print("🔍 EXPLORADOR DE DATASET - datos.gob.ar")
print("=" * 80)
print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Argumentos
parser = argparse.ArgumentParser(description='Explorar detalles de un dataset')
parser.add_argument('--id', type=str, required=True, help='ID del dataset a explorar')
args = parser.parse_args()

dataset_id = args.id
print(f"\n🔎 Explorando dataset: {dataset_id}")

# API
BASE_URL = "https://datos.gob.ar/api/3"
url = f"{BASE_URL}/action/package_show"
params = {'id': dataset_id}

try:
    response = requests.get(url, params=params, timeout=30)

    if response.status_code == 200:
        data = response.json()

        if data.get('success') and data.get('result'):
            dataset = data['result']

            print(f"\n✅ Dataset encontrado")
            print("\n" + "=" * 80)
            print("📋 INFORMACIÓN GENERAL")
            print("=" * 80)

            print(f"\n📌 Título: {dataset.get('title', 'N/A')}")
            print(f"🆔 ID: {dataset.get('id', 'N/A')}")
            print(f"🏢 Organización: {dataset.get('organization', {}).get('title', 'N/A')}")
            print(f"📝 Descripción: {dataset.get('notes', 'N/A')[:200]}...")
            print(f"🏷️  Tags: {', '.join([t['display_name'] for t in dataset.get('tags', [])])}")
            print(f"📅 Creado: {dataset.get('metadata_created', 'N/A')}")
            print(f"🔄 Actualizado: {dataset.get('metadata_modified', 'N/A')}")
            print(f"🌐 URL: {dataset.get('url', 'N/A')}")

            # Recursos (distribuciones)
            resources = dataset.get('resources', [])

            if resources:
                print("\n" + "=" * 80)
                print(f"📦 RECURSOS DISPONIBLES ({len(resources)})")
                print("=" * 80)

                for idx, resource in enumerate(resources, 1):
                    print(f"\n{idx}. {resource.get('name', 'Sin nombre')}")
                    print(f"   📄 Formato: {resource.get('format', 'N/A')}")
                    print(f"   📊 Tipo: {resource.get('mimetype', 'N/A')}")
                    print(f"   🔗 URL: {resource.get('url', 'N/A')}")
                    print(f"   📏 Tamaño: {resource.get('size', 'N/A')}")
                    print(f"   📅 Última modificación: {resource.get('last_modified', 'N/A')}")
                    print(f"   📝 Descripción: {resource.get('description', 'N/A')[:100]}")

                    # Si es CSV o JSON, mostrar que se puede descargar
                    fmt = resource.get('format', '').upper()
                    if fmt in ['CSV', 'JSON', 'XLSX', 'XLS']:
                        print(f"   💾 DESCARGABLE - Comando:")
                        print(f"      wget '{resource.get('url')}' -O {resource.get('name', 'datos')}.{fmt.lower()}")

                # Guardar recursos en JSON
                output_file = f"dataset_{dataset_id}_recursos.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(resources, f, indent=2, ensure_ascii=False)

                print(f"\n💾 Recursos guardados en: {output_file}")

                # Análisis de formatos
                print("\n" + "=" * 80)
                print("📊 ANÁLISIS DE FORMATOS")
                print("=" * 80)

                formatos = {}
                for r in resources:
                    fmt = r.get('format', 'DESCONOCIDO').upper()
                    formatos[fmt] = formatos.get(fmt, 0) + 1

                for fmt, count in sorted(formatos.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {fmt}: {count} archivo(s)")

                # URLs de descarga directa
                csv_resources = [r for r in resources if r.get('format', '').upper() == 'CSV']
                json_resources = [r for r in resources if r.get('format', '').upper() == 'JSON']

                if csv_resources or json_resources:
                    print("\n" + "=" * 80)
                    print("🚀 PRÓXIMOS PASOS SUGERIDOS")
                    print("=" * 80)

                    if csv_resources:
                        print(f"\n✅ Encontrados {len(csv_resources)} archivos CSV")
                        print("   Puedes crear un script para:")
                        print("   1. Descargar los CSVs automáticamente")
                        print("   2. Parsear y cargar a PostgreSQL")
                        print("   3. Actualizar el dashboard")

                    if json_resources:
                        print(f"\n✅ Encontrados {len(json_resources)} archivos JSON")
                        print("   Puedes consumir directamente desde la URL")

            else:
                print("\n⚠️ Este dataset no tiene recursos disponibles")

            print("\n" + "=" * 80)
            print("✅ EXPLORACIÓN COMPLETADA")
            print("=" * 80)

        else:
            print(f"\n❌ Dataset no encontrado: {dataset_id}")
            print("💡 Verifica el ID en: https://datos.gob.ar")

    else:
        print(f"\n❌ Error HTTP {response.status_code}")
        print(f"   Respuesta: {response.text[:200]}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
