"""
Script inteligente para cargar datos.
Consulta primero qué datos están disponibles y luego los carga.
"""
from backend.api_clients import INDECClient, BCRAClient
from datetime import date, timedelta
import requests

print("=" * 70)
print("📊 Carga Inteligente de Datos - INDEC y BCRA")
print("=" * 70)

# ==================== INDEC ====================
print("\n🔍 [INDEC] Consultando series disponibles...")

indec = INDECClient()

# Probar una serie para obtener metadata
try:
    # Consultar IPC sin fechas para ver qué hay disponible
    response = indec.get_series(
        series_id='148.3_INIVELNAL_DICI_M_26',  # IPC Nacional
        formato='json'
    )

    if response and 'data' in response:
        data_points = response['data']

        if data_points:
            # Extraer primera y última fecha disponible
            fechas = [punto[0] for punto in data_points]
            fecha_min = min(fechas)
            fecha_max = max(fechas)

            print(f"✅ IPC disponible desde: {fecha_min} hasta: {fecha_max}")
            print(f"   Total de puntos de datos: {len(data_points)}")

            # Usar últimos 12 meses disponibles
            fecha_max_obj = date.fromisoformat(fecha_max[:10])
            fecha_desde = fecha_max_obj - timedelta(days=365)

            print(f"\n📥 Cargando INDEC (últimos 12 meses)...")
            print(f"   Desde: {fecha_desde}")
            print(f"   Hasta: {fecha_max_obj}")

            result_indec = indec.sync_all_indicators(fecha_desde=fecha_desde)

            # Mostrar resumen
            print("\n📊 RESUMEN INDEC:")
            for indicador, info in result_indec['indicadores'].items():
                status = info.get('status', 'unknown')
                if status == 'success':
                    records = info.get('records_saved', 0)
                    obtained = info.get('records_obtained', 0)
                    print(f"   ✅ {indicador}: {records} guardados (de {obtained} obtenidos)")
                else:
                    print(f"   ❌ {indicador}: {info.get('message', 'Error')}")
        else:
            print("⚠️  No hay datos disponibles en la serie IPC")
    else:
        print("❌ No se pudo consultar la serie IPC")

except Exception as e:
    print(f"❌ Error consultando INDEC: {e}")

# ==================== BCRA ====================
print("\n" + "=" * 70)
print("🔍 [BCRA] Intentando consultar datos...")

bcra = BCRAClient()

# BCRA tiene problemas con errores 500, intentar con fechas fijas conservadoras
print("   Usando fechas conservadoras (últimos 3 meses de 2024)...")

try:
    result_bcra = bcra.sync_all_indicators(
        fecha_desde=date(2024, 8, 1),
        fecha_hasta=date(2024, 10, 31)  # Octubre 2024
    )

    print("\n📊 RESUMEN BCRA:")
    if result_bcra['records_saved'] > 0:
        print(f"   ✅ Registros guardados: {result_bcra['records_saved']}")
    else:
        print("   ⚠️  No se guardaron registros (API con errores 500)")
        print("   💡 La API del BCRA está presentando problemas temporales")

except Exception as e:
    print(f"   ❌ Error: {e}")

# ==================== RESUMEN FINAL ====================
print("\n" + "=" * 70)
print("✅ PROCESO COMPLETADO")
print("=" * 70)
print("\n💡 Próximos pasos:")
print("   1. Ve al dashboard de Streamlit")
print("   2. Presiona 'C' para limpiar cache")
print("   3. Revisa la pestaña INDEC para ver los datos cargados")
print("\n" + "=" * 70)
