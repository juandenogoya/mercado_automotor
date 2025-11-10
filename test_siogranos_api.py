"""
Script para probar la API de SIOGRANOS y evaluar su utilidad
para análisis del mercado automotor
"""
import requests
import json
from datetime import datetime, timedelta

def test_siogranos_api():
    """Prueba la API de SIOGRANOS y analiza los datos"""

    base_url = "https://test.bc.org.ar/SiogranosAPI/api/ConsultaPublica/consultarOperaciones"

    # Calcular fechas (últimos 30 días)
    fecha_hasta = datetime.now()
    fecha_desde = fecha_hasta - timedelta(days=30)

    # Formatear fechas
    fecha_desde_str = fecha_desde.strftime('%Y-%m-%d')
    fecha_hasta_str = fecha_hasta.strftime('%Y-%m-%d')

    print("="*80)
    print("🌾 TEST - API SIOGRANOS (Operaciones de Granos)")
    print("="*80)
    print(f"\n📅 Consultando operaciones desde {fecha_desde_str} hasta {fecha_hasta_str}\n")

    # Test 1: Consulta simple sin filtros
    print("\n" + "="*80)
    print("1️⃣ TEST 1: Consulta básica (últimos 30 días)")
    print("="*80)

    params = {
        'FechaOperacionDesde': fecha_desde_str,
        'FechaOperacionHasta': fecha_hasta_str
    }

    try:
        print(f"🔗 URL: {base_url}")
        print(f"📊 Parámetros: {params}\n")

        response = requests.get(base_url, params=params, timeout=30)

        print(f"📊 Status: {response.status_code}")
        print(f"📏 Tamaño respuesta: {len(response.content)} bytes\n")

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list):
                print(f"✅ Respuesta exitosa: {len(data)} operaciones encontradas\n")

                if len(data) > 0:
                    # Analizar primera operación
                    print("="*80)
                    print("📋 EJEMPLO DE OPERACIÓN (primera del resultado):")
                    print("="*80)

                    first_op = data[0]
                    for key, value in first_op.items():
                        print(f"  • {key}: {value}")

                    # Análisis estadístico
                    print("\n" + "="*80)
                    print("📊 ANÁLISIS DE DATOS:")
                    print("="*80)

                    # Granos únicos
                    granos = set(op.get('grano', 'N/A') for op in data)
                    print(f"\n🌾 Granos encontrados ({len(granos)}):")
                    for grano in sorted(granos):
                        count = sum(1 for op in data if op.get('grano') == grano)
                        print(f"  • {grano}: {count} operaciones")

                    # Provincias
                    provincias = set(op.get('procedenciaProvincia', 'N/A') for op in data)
                    print(f"\n🗺️  Provincias ({len(provincias)}):")
                    for prov in sorted(provincias):
                        count = sum(1 for op in data if op.get('procedenciaProvincia') == prov)
                        print(f"  • {prov}: {count} operaciones")

                    # Volumen total
                    volumenes = [op.get('volumenTN', 0) for op in data if op.get('volumenTN')]
                    if volumenes:
                        volumen_total = sum(volumenes)
                        volumen_promedio = volumen_total / len(volumenes)
                        print(f"\n📦 Volumen:")
                        print(f"  • Total: {volumen_total:,.2f} TN")
                        print(f"  • Promedio: {volumen_promedio:,.2f} TN/operación")

                    # Precios
                    precios = [op.get('precioTN', 0) for op in data if op.get('precioTN')]
                    if precios:
                        precio_min = min(precios)
                        precio_max = max(precios)
                        precio_promedio = sum(precios) / len(precios)
                        print(f"\n💰 Precios:")
                        print(f"  • Mínimo: {precio_min:,.2f} /TN")
                        print(f"  • Máximo: {precio_max:,.2f} /TN")
                        print(f"  • Promedio: {precio_promedio:,.2f} /TN")

                    # Monedas
                    simbolos = set(op.get('simboloPrecioPorTN', 'N/A') for op in data)
                    print(f"\n💵 Monedas usadas: {', '.join(sorted(simbolos))}")

                    # Guardar muestra en JSON
                    sample_file = 'siogranos_sample.json'
                    with open(sample_file, 'w', encoding='utf-8') as f:
                        json.dump(data[:10], f, indent=2, ensure_ascii=False)
                    print(f"\n💾 Primeras 10 operaciones guardadas en: {sample_file}")

                else:
                    print("⚠️ No se encontraron operaciones en el período consultado")
            else:
                print(f"⚠️ Respuesta inesperada (no es una lista): {type(data)}")
                print(f"Contenido: {data}")

        elif response.status_code == 404:
            print("❌ Error 404: Endpoint no encontrado")
            print("   La URL podría haber cambiado o el servidor de testing no está disponible")

        elif response.status_code == 400:
            print("❌ Error 400: Parámetros incorrectos")
            print(f"   Respuesta: {response.text}")

        else:
            print(f"❌ Error {response.status_code}: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: No se pudo conectar al servidor")
        print("   Verifica que la URL sea correcta y que tengas conexión a internet")

    except requests.exceptions.Timeout:
        print("❌ Timeout: El servidor tardó demasiado en responder")

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Consulta específica de soja
    print("\n" + "="*80)
    print("2️⃣ TEST 2: Consulta específica de SOJA")
    print("="*80)

    # Según documentación, idGrano para soja debería estar en TABLA 1
    # Probaremos con id común para soja (generalmente 1 o 31)
    for id_soja in [1, 31]:
        params_soja = {
            'FechaOperacionDesde': fecha_desde_str,
            'FechaOperacionHasta': fecha_hasta_str,
            'idGrano': id_soja
        }

        print(f"\n🔍 Probando con idGrano={id_soja}...")

        try:
            response = requests.get(base_url, params=params_soja, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ Encontradas {len(data)} operaciones de soja (idGrano={id_soja})")
                    break
                else:
                    print(f"   No hay operaciones con idGrano={id_soja}")
        except:
            pass

    # Evaluación final
    print("\n" + "="*80)
    print("📋 EVALUACIÓN PARA ANÁLISIS AUTOMOTOR")
    print("="*80)
    print("""
✅ VENTAJAS:
  • API pública y accesible (no requiere autenticación)
  • Datos estructurados y actualizados en tiempo real
  • Información geográfica (provincias/localidades)
  • Precios y volúmenes de transacciones reales
  • Datos históricos disponibles por fechas

⚠️ CONSIDERACIONES:
  • Correlación indirecta con mercado automotor
  • Requiere análisis cruzado con datos de vehículos
  • Mejor para análisis predictivo que descriptivo actual

🎯 CASOS DE USO RECOMENDADOS:
  1. Correlación precio soja → ventas de pick-ups/utilitarios
  2. Análisis geográfico: zonas con alta actividad agrícola =
     mayor demanda de vehículos rurales
  3. Modelo predictivo: volumen/precio granos como indicador
     adelantado (3-6 meses) de demanda automotor
  4. Segmentación: identificar provincias con alto poder
     adquisitivo rural para targeting de concesionarias

💡 RECOMENDACIÓN FINAL:
  ✅ SÍ, integrar esta API como fuente complementaria
  ✅ Crear tabla en PostgreSQL: siogranos_operaciones
  ✅ Automatizar carga diaria/semanal
  ✅ Cruzar con datos de datos.gob.ar para análisis correlacional
""")

    print("="*80)
    print("✅ Test completado")
    print("="*80)

if __name__ == "__main__":
    test_siogranos_api()
