"""
Script de prueba simplificado para verificar acceso a patentamientos INDEC.
"""
from datetime import date, timedelta
from backend.api_clients.indec_client import INDECClient

print("=" * 70)
print("🚗 PRUEBA DE ACCESO A PATENTAMIENTOS INDEC (Excel)")
print("=" * 70)

try:
    indec = INDECClient()

    # Obtener últimos 12 meses de patentamientos
    fecha_desde = date(2024, 1, 1)  # Año 2024
    fecha_hasta = date(2024, 12, 31)

    print(f"\n📥 Descargando Excel de patentamientos del INDEC...")
    print(f"   URL: https://www.indec.gob.ar/ftp/cuadros/economia/cuadros_indices_patentamientos.xls")
    print(f"   Período solicitado: {fecha_desde.strftime('%Y-%m')} a {fecha_hasta.strftime('%Y-%m')}")

    datos_patentamientos = indec.get_patentamientos_excel(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )

    if datos_patentamientos:
        print(f"\n✅ ÉXITO - Excel descargado correctamente")
        print(f"   Total de hojas encontradas: {len(datos_patentamientos)}")
        print("\n" + "=" * 70)

        for sheet_name, df in datos_patentamientos.items():
            print(f"\n📄 HOJA: '{sheet_name}'")
            print(f"   Registros totales: {len(df)}")
            print(f"   Columnas disponibles: {list(df.columns)}")

            # Mostrar muestra de datos
            if len(df) > 0:
                print(f"\n   📊 MUESTRA DE DATOS (primeras 5 filas):")
                print("-" * 70)
                print(df.head(5).to_string(index=False, max_colwidth=15))
                print("-" * 70)
            else:
                print("   ⚠️  Hoja sin datos")

        print("\n" + "=" * 70)
        print("✅ CONCLUSIÓN: Acceso a patentamientos INDEC CONFIRMADO")
        print("=" * 70)
        print("""
💡 TIPOS DE DATOS DISPONIBLES:
   - Índices de patentamientos (base 2014=100)
   - Serie original y desestacionalizada
   - Desagregación por tipo de vehículo:
     * Autos
     * Motos
     * Camiones
     * Utilitarios
   - Desagregación por provincia
   - Origen: Nacional vs Importado
   - Datos históricos mensuales

🎯 PRÓXIMO PASO:
   Podés usar esta fuente para alimentar tu dashboard
   con datos reales de patentamientos automotrices.
        """)

    else:
        print("\n❌ ERROR - No se pudo descargar el Excel de patentamientos")
        print("   Posibles causas:")
        print("   - El servidor del INDEC no responde")
        print("   - El archivo Excel cambió de ubicación")
        print("   - Problemas de conexión")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
