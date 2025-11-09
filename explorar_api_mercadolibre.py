"""
Explorador completo de API de MercadoLibre
Descubre toda la información disponible para análisis del mercado automotor

EJECUCIÓN:
python explorar_api_mercadolibre.py

API MercadoLibre: https://developers.mercadolibre.com.ar/
"""

import requests
import json
from datetime import datetime
from pathlib import Path

# Configuración
BASE_URL = "https://api.mercadolibre.com"
SITE_ID = "MLA"  # Argentina
CATEGORIA_AUTOS = "MLA1743"

# Crear directorio output
output_dir = Path(__file__).parent / "exploracion_mercadolibre"
output_dir.mkdir(exist_ok=True)

print("=" * 80)
print("🔍 EXPLORADOR API MERCADOLIBRE - MERCADO AUTOMOTOR")
print("=" * 80)
print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)


def guardar_json(data, nombre):
    """Guardar resultado en JSON"""
    filepath = output_dir / f"{nombre}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"   💾 Guardado: {filepath}")


print("\n" + "=" * 80)
print("1️⃣ EXPLORACIÓN DE CATEGORÍAS")
print("=" * 80)

# 1. Categoría principal de autos
print(f"\n📂 Categoría principal: {CATEGORIA_AUTOS}")
url = f"{BASE_URL}/categories/{CATEGORIA_AUTOS}"
response = requests.get(url, timeout=30)

if response.status_code == 200:
    categoria_data = response.json()
    print(f"   ✅ Nombre: {categoria_data['name']}")
    print(f"   📊 Total items: {categoria_data.get('total_items_in_this_category', 0):,}")

    # Subcategorías
    print(f"\n   📁 Subcategorías ({len(categoria_data.get('children_categories', []))}):")
    for subcat in categoria_data.get('children_categories', [])[:10]:
        print(f"      • {subcat['id']}: {subcat['name']} ({subcat.get('total_items_in_this_category', 0):,} items)")

    guardar_json(categoria_data, "categoria_autos_principal")

    # Explorar subcategoría de autos usados
    for subcat in categoria_data.get('children_categories', []):
        if 'usado' in subcat['name'].lower() or 'venta' in subcat['name'].lower():
            print(f"\n   🔍 Explorando subcategoría: {subcat['name']}")
            subcat_url = f"{BASE_URL}/categories/{subcat['id']}"
            subcat_response = requests.get(subcat_url, timeout=30)
            if subcat_response.status_code == 200:
                subcat_data = subcat_response.json()
                print(f"      Total items: {subcat_data.get('total_items_in_this_category', 0):,}")
                guardar_json(subcat_data, f"subcategoria_{subcat['id']}")


print("\n" + "=" * 80)
print("2️⃣ ATRIBUTOS DISPONIBLES")
print("=" * 80)

# 2. Atributos de la categoría
print("\n📋 Atributos que se pueden usar para filtrar/buscar:")
if 'attributes' in categoria_data:
    for attr in categoria_data['attributes'][:15]:
        print(f"   • {attr['id']}: {attr['name']}")
        if attr.get('values'):
            print(f"     Valores: {len(attr['values'])} opciones")
            # Mostrar algunos valores de ejemplo
            for val in attr['values'][:3]:
                print(f"       - {val['name']}")

    # Guardar todos los atributos
    atributos_completos = {attr['id']: attr for attr in categoria_data.get('attributes', [])}
    guardar_json(atributos_completos, "atributos_disponibles")


print("\n" + "=" * 80)
print("3️⃣ BÚSQUEDA DE PRUEBA")
print("=" * 80)

# 3. Búsqueda de ejemplo - Toyota
print("\n🔍 Búsqueda de prueba: Toyota (primeros 10 resultados)")
search_url = f"{BASE_URL}/sites/{SITE_ID}/search"
params = {
    'category': CATEGORIA_AUTOS,
    'q': 'Toyota',
    'limit': 10
}

search_data = {}
try:
    response = requests.get(search_url, params=params, timeout=30)
    if response.status_code == 200:
        search_data = response.json()

        print(f"   ✅ Total resultados: {search_data['paging']['total']:,}")
        print(f"   📊 Mostrando {len(search_data['results'])} de {search_data['paging']['total']:,}")

        print(f"\n   📄 Primeros resultados:")
        for i, item in enumerate(search_data['results'][:5], 1):
            print(f"\n   {i}. {item['title']}")
            print(f"      💰 Precio: ${item['price']:,.0f} {item['currency_id']}")
            print(f"      📍 Ubicación: {item.get('location', {}).get('city', {}).get('name', 'N/A')}")
            print(f"      🏷️ Condición: {item['condition']}")
            print(f"      🆔 ID: {item['id']}")

        # Analizar estructura de un resultado
        if search_data.get('results'):
            print(f"\n   🔍 Estructura completa del primer resultado:")
            primer_item = search_data['results'][0]
            print(f"      Campos disponibles: {list(primer_item.keys())}")

            # Atributos del vehículo
            if 'attributes' in primer_item:
                print(f"\n      📋 Atributos del vehículo ({len(primer_item['attributes'])}):")
                for attr in primer_item['attributes'][:10]:
                    print(f"         • {attr['id']}: {attr.get('value_name', 'N/A')}")

            guardar_json(search_data, "busqueda_toyota_ejemplo")
    else:
        print(f"   ❌ Error HTTP {response.status_code}")
except Exception as e:
    print(f"   ❌ Error en búsqueda: {e}")


print("\n" + "=" * 80)
print("4️⃣ DETALLE DE UN ITEM")
print("=" * 80)

# 4. Detalle completo de un item
if search_data.get('results'):
    item_id = search_data['results'][0]['id']
    print(f"\n🔍 Obteniendo detalle completo del item: {item_id}")

    item_url = f"{BASE_URL}/items/{item_id}"
    response = requests.get(item_url, timeout=30)

    if response.status_code == 200:
        item_detail = response.json()

        print(f"   ✅ Título: {item_detail['title']}")
        print(f"   💰 Precio: ${item_detail['price']:,.0f}")
        print(f"   📷 Imágenes: {len(item_detail.get('pictures', []))}")
        print(f"   📝 Descripción disponible: {'Sí' if item_detail.get('descriptions') else 'No'}")

        print(f"\n   📊 Campos completos disponibles:")
        print(f"      {list(item_detail.keys())}")

        # Atributos técnicos
        print(f"\n   🔧 Atributos técnicos ({len(item_detail.get('attributes', []))}):")
        for attr in item_detail.get('attributes', [])[:15]:
            print(f"      • {attr.get('name', 'N/A')}: {attr.get('value_name', 'N/A')}")

        guardar_json(item_detail, "detalle_item_completo")

        # Obtener descripción
        desc_url = f"{BASE_URL}/items/{item_id}/description"
        desc_response = requests.get(desc_url, timeout=30)
        if desc_response.status_code == 200:
            descripcion = desc_response.json()
            print(f"\n   📝 Descripción ({len(descripcion.get('plain_text', ''))} caracteres)")
            print(f"      {descripcion.get('plain_text', '')[:200]}...")
            guardar_json(descripcion, "descripcion_item")
else:
    print("\n   ⚠️ No se pudo obtener detalle (la búsqueda falló)")


print("\n" + "=" * 80)
print("5️⃣ FILTROS DISPONIBLES")
print("=" * 80)

# 5. Filtros disponibles en búsqueda
print("\n🎛️ Filtros disponibles para búsquedas:")

if search_data.get('available_filters'):
    print(f"\n   📊 Total filtros: {len(search_data['available_filters'])}")

    for filtro in search_data['available_filters'][:10]:
        print(f"\n   • {filtro['id']}: {filtro['name']}")
        if filtro.get('values'):
            print(f"     Opciones ({len(filtro['values'])}):")
            for val in filtro['values'][:5]:
                print(f"       - {val['name']} ({val.get('results', 0):,} resultados)")

    guardar_json(search_data['available_filters'], "filtros_disponibles")
else:
    print("   ⚠️ No se pudieron obtener filtros (la búsqueda falló)")


print("\n" + "=" * 80)
print("6️⃣ ANÁLISIS DE MERCADO")
print("=" * 80)

# 6. Análisis rápido del mercado
print("\n📊 Análisis rápido del mercado:")

# Búsqueda por condición
for condicion in ['new', 'used']:
    params_cond = {
        'category': CATEGORIA_AUTOS,
        'condition': condicion,
        'limit': 1
    }
    response = requests.get(search_url, params=params_cond, timeout=30)
    if response.status_code == 200:
        data = response.json()
        label = "0km" if condicion == 'new' else "Usados"
        print(f"   • {label}: {data['paging']['total']:,} publicaciones")

# Top marcas (aproximado via búsqueda)
print(f"\n   🏆 Top marcas por cantidad de publicaciones:")
marcas_top = ['Toyota', 'Ford', 'Volkswagen', 'Chevrolet', 'Fiat', 'Renault']
resultados_marcas = {}

for marca in marcas_top:
    params_marca = {
        'category': CATEGORIA_AUTOS,
        'q': marca,
        'limit': 1
    }
    response = requests.get(search_url, params=params_marca, timeout=30)
    if response.status_code == 200:
        data = response.json()
        resultados_marcas[marca] = data['paging']['total']
        print(f"      • {marca}: {data['paging']['total']:,} publicaciones")

guardar_json(resultados_marcas, "analisis_marcas_top")


print("\n" + "=" * 80)
print("7️⃣ INFORMACIÓN DISPONIBLE - RESUMEN")
print("=" * 80)

print("""
✅ DATOS DISPONIBLES EN API MERCADOLIBRE:

📊 Por Item/Publicación:
   • ID único del listing
   • Título y descripción completa
   • Precio (actual e histórico si scrapeamos periódicamente)
   • Moneda (ARS, USD)
   • Condición (nuevo/usado)
   • Estado de la publicación (activo, pausado, finalizado)

🚗 Características del Vehículo:
   • Marca y modelo
   • Año
   • Kilómetros
   • Tipo de combustible
   • Transmisión
   • Tipo de vehículo
   • Color
   • Puertas
   • Versión/trim

📍 Ubicación:
   • Provincia
   • Ciudad
   • Coordenadas (lat/lng) si disponible

💰 Información Comercial:
   • Precio de lista
   • Tipo de vendedor (particular/concesionaria)
   • Cantidad de visitas
   • Cantidad de ventas del vendedor
   • Reputación del vendedor

📷 Media:
   • Imágenes (múltiples)
   • URLs de imágenes en diferentes resoluciones

🔍 Metadata:
   • Fecha de publicación
   • Fecha de última actualización
   • Categoría y subcategoría
   • Tags y keywords

📈 ANÁLISIS POSIBLES:

1. Precios de mercado por marca/modelo/año
2. Evolución de precios (scraping periódico)
3. Distribución geográfica de oferta
4. Análisis de depreciación por km y año
5. Modelos más ofertados
6. Comparación 0km vs usados
7. Tendencias de mercado
8. Análisis de vendedores
9. Correlación precio/características
10. Predicción de precios

""")

print("=" * 80)
print("✅ EXPLORACIÓN COMPLETADA")
print("=" * 80)
print(f"\n📁 Archivos JSON guardados en: {output_dir}")
print("\n🎯 Próximos pasos:")
print("   1. Crear script de scraping periódico")
print("   2. Diseñar base de datos para históricos")
print("   3. Implementar análisis de precios")
print("   4. Dashboard de visualización")
print("=" * 80)
