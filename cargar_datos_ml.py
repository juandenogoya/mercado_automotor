"""
Script para cargar datos de MercadoLibre.
Obtiene snapshots de:
- Autos nuevos (0km)
- Autos usados
- Motos nuevas
- Motos usadas
"""
from backend.api_clients.mercadolibre_client import MercadoLibreClient
from datetime import date

print("=" * 60)
print("🛒 Carga de Datos - MercadoLibre")
print("=" * 60)

client = MercadoLibreClient()

# Marcas principales de autos en Argentina
marcas_autos = [
    'Toyota', 'Ford', 'Volkswagen', 'Chevrolet', 'Fiat',
    'Renault', 'Peugeot', 'Nissan', 'Jeep', 'Honda'
]

# Marcas principales de motos
marcas_motos = [
    'Honda', 'Yamaha', 'Kawasaki', 'Suzuki', 'Bajaj',
    'Motomel', 'Zanella', 'Corven', 'Guerrero', 'Gilera'
]

print(f"\n📅 Fecha: {date.today()}")
print(f"🚗 Marcas de autos: {len(marcas_autos)}")
print(f"🏍️  Marcas de motos: {len(marcas_motos)}")
print("-" * 60)

# Realizar snapshot del mercado
print("\n🔄 Ejecutando snapshot del mercado...")
print("   (Esto puede tardar varios minutos debido al rate limiting)\n")

result = client.scrape_market_snapshot(
    marcas=marcas_autos,  # Solo autos por ahora
    max_items_por_marca=30  # Limitar para no exceder rate limit
)

print("\n" + "=" * 60)
print("📊 RESUMEN DE CARGA")
print("=" * 60)
print(f"✅ Estado: {result['status']}")
print(f"📅 Fecha snapshot: {result['fecha_snapshot']}")
print(f"🏷️  Marcas procesadas: {result['marcas_procesadas']}")
print(f"📦 Items scraped: {result['items_scraped']}")
print(f"💾 Items guardados en BD: {result['items_saved']}")
print("=" * 60)

# Mostrar estadísticas adicionales
if result['items_saved'] > 0:
    print("\n✅ Datos cargados exitosamente")
    print("💡 Ahora puedes ver los datos en el dashboard (pestaña MercadoLibre)")
    print("💡 Refresca el navegador (F5) para ver los datos actualizados")
else:
    print("\n⚠️  No se guardaron nuevos items")
    print("💡 Puede que ya existan snapshots para hoy")
    print("💡 O que la API de MercadoLibre no esté respondiendo")

print("\n" + "=" * 60)
