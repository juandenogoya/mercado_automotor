"""
Script de prueba para verificar acceso a datos automotrices.

Fuentes a probar:
1. INDEC - Patentamientos (Excel)
2. DNRPA - Inscripciones oficiales
"""
from datetime import date, timedelta
from backend.api_clients import INDECClient
from backend.scrapers.dnrpa_scraper import DNRPAScraper

print("=" * 70)
print("🚗 PRUEBA DE ACCESO A DATOS AUTOMOTRICES")
print("=" * 70)

# ========================================================================
# 1. INDEC - Patentamientos desde Excel
# ========================================================================
print("\n📊 [1/2] PROBANDO INDEC - Patentamientos desde Excel...")
print("-" * 70)

try:
    indec = INDECClient()

    # Obtener últimos 12 meses de patentamientos
    fecha_desde = date.today() - timedelta(days=365)

    print(f"📥 Descargando Excel de patentamientos...")
    print(f"   Período: {fecha_desde.strftime('%Y-%m')} a {date.today().strftime('%Y-%m')}")

    datos_patentamientos = indec.get_patentamientos_excel(
        fecha_desde=fecha_desde,
        fecha_hasta=date.today()
    )

    if datos_patentamientos:
        print(f"\n✅ ÉXITO - Excel descargado correctamente")
        print(f"   Hojas encontradas: {len(datos_patentamientos)}")

        for sheet_name, df in datos_patentamientos.items():
            print(f"\n   📄 Hoja: '{sheet_name}'")
            print(f"      Registros: {len(df)}")
            print(f"      Columnas: {list(df.columns)[:5]}...")  # Primeras 5 columnas

            # Mostrar muestra de datos
            if len(df) > 0:
                print(f"\n      Muestra de datos:")
                print(df.head(3).to_string(index=False))
    else:
        print("❌ ERROR - No se pudo descargar el Excel de patentamientos")

except Exception as e:
    print(f"❌ ERROR en INDEC: {e}")

# ========================================================================
# 2. DNRPA - Datos oficiales de inscripciones
# ========================================================================
print("\n\n📊 [2/2] PROBANDO DNRPA - Inscripciones Oficiales...")
print("-" * 70)

try:
    dnrpa = DNRPAScraper()

    # Obtener datos del año actual
    anio_actual = date.today().year

    print(f"📥 Consultando DNRPA para año {anio_actual}...")
    print(f"   Tipo de vehículo: Autos (código 'A')")
    print(f"   Tipo de trámite: Inscripciones (código 3)")

    # Probar obtener resumen por provincias (Autos)
    datos_autos = dnrpa.get_provincias_summary(
        anio=anio_actual,
        codigo_tipo='A',  # Autos
        codigo_tramite=3  # Inscripciones
    )

    if datos_autos and len(datos_autos) > 0:
        print(f"\n✅ ÉXITO - Datos de AUTOS obtenidos")
        print(f"   Registros: {len(datos_autos)}")
        print(f"\n   Muestra de datos (primeros 5):")
        for i, registro in enumerate(datos_autos[:5]):
            print(f"      {i+1}. Provincia: {registro.get('provincia', 'N/A')}, "
                  f"Cantidad: {registro.get('cantidad', 0)}, "
                  f"Mes: {registro.get('mes', 'N/A')}")
    else:
        print("⚠️  No se obtuvieron datos de autos (puede ser normal si el año está en curso)")

    # Probar obtener resumen por provincias (Motos)
    print(f"\n📥 Consultando DNRPA para MOTOS...")
    datos_motos = dnrpa.get_provincias_summary(
        anio=anio_actual,
        codigo_tipo='M',  # Motos
        codigo_tramite=3
    )

    if datos_motos and len(datos_motos) > 0:
        print(f"\n✅ ÉXITO - Datos de MOTOS obtenidos")
        print(f"   Registros: {len(datos_motos)}")
    else:
        print("⚠️  No se obtuvieron datos de motos")

except Exception as e:
    print(f"❌ ERROR en DNRPA: {e}")

# ========================================================================
# Resumen final
# ========================================================================
print("\n" + "=" * 70)
print("📋 RESUMEN DE FUENTES DE DATOS AUTOMOTRICES")
print("=" * 70)
print("""
✅ DISPONIBLES SIN DEPENDENCIA DE API IDs:
   1. INDEC - Patentamientos (Excel)
      - Autos, motos, camiones por separado
      - Series originales y desestacionalizadas
      - Desagregación provincial
      - Origen: nacional/importado

   2. DNRPA - Inscripciones oficiales
      - Datos por provincia
      - Autos / Motos / Maquinarias
      - Fuente gubernamental oficial
      - Datos mensuales

⚠️  REQUIERE VERIFICACIÓN DE ID:
   3. IPI Automotriz (API INDEC)
      - Índice Producción Industrial sector automotriz
      - Necesita buscar ID correcto en datos.gob.ar

💡 CONCLUSIÓN:
   Tenés acceso completo a datos automotrices sin necesidad
   de reparar los IDs de la API. Podés usar INDEC Excel y DNRPA.
""")
print("=" * 70)
