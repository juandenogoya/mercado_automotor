"""
Test completo del DNRPA scraper
Verificar que devuelve el DataFrame correctamente
"""
import sys
sys.path.append('/home/user/mercado_automotor')

from backend.scrapers.dnrpa_scraper import DNRPAScraper

print("=" * 80)
print("🧪 TEST COMPLETO - DNRPA Scraper")
print("=" * 80)

# Inicializar scraper
scraper = DNRPAScraper()

# Probar scraping de resumen provincial
print("\n📊 Obteniendo resumen provincial para Autos 2024...")
df = scraper.get_provincias_summary(
    anio=2024,
    codigo_tipo='A',  # Autos
    codigo_tramite=3  # Inscripciones
)

if df is not None and not df.empty:
    print(f"\n✅ DataFrame obtenido exitosamente!")
    print(f"   Forma: {df.shape}")
    print(f"   Columnas: {list(df.columns)}")

    print("\n📋 Primeras 5 provincias:")
    print(df.head(5).to_string())

    print("\n📊 Tipos de datos:")
    print(df.dtypes)

    # Verificar que tiene las columnas esperadas
    expected_cols = ['Provincia / Mes', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                     'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic', 'Total']

    if list(df.columns) == expected_cols:
        print("\n✅ Columnas correctas!")
    else:
        print(f"\n⚠️ Columnas no coinciden")
        print(f"   Esperadas: {expected_cols}")
        print(f"   Recibidas: {list(df.columns)}")

    # Verificar que tiene datos numéricos
    print(f"\n🔢 Valores en columna 'Ene':")
    print(df['Ene'].head(5))

else:
    print("\n❌ No se obtuvo DataFrame")

print("\n" + "=" * 80)
print("✅ TEST COMPLETADO")
print("=" * 80)
