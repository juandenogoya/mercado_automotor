"""
Script completo de carga de datos automotrices.

Fuentes integradas:
1. INDEC - Patentamientos (Excel directo)
2. DNRPA - Inscripciones oficiales
3. IPI Automotriz - Producción industrial (cuando se encuentre el ID correcto)

USO:
    python cargar_datos_automotrices.py
"""
from datetime import date, timedelta
from backend.api_clients.indec_client import INDECClient
from backend.models.patentamientos import Patentamiento
from backend.utils.database import get_db
from sqlalchemy import text
import pandas as pd

print("=" * 80)
print("🚗 CARGA DE DATOS AUTOMOTRICES - ARGENTINA")
print("=" * 80)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
# Definir período de carga (últimos 24 meses)
fecha_hasta = date.today()
fecha_desde = fecha_hasta - timedelta(days=730)  # ~24 meses

print(f"\n⚙️  CONFIGURACIÓN:")
print(f"   Período: {fecha_desde.strftime('%Y-%m-%d')} a {fecha_hasta.strftime('%Y-%m-%d')}")
print(f"   Base de datos: PostgreSQL (mercado_automotor)")

# ============================================================================
# 1. INDEC - PATENTAMIENTOS (Excel)
# ============================================================================
print("\n" + "=" * 80)
print("📊 [1/3] INDEC - PATENTAMIENTOS (Descarga desde Excel)")
print("=" * 80)

try:
    indec = INDECClient()

    print(f"\n📥 Descargando Excel de patentamientos...")
    print(f"   URL: https://www.indec.gob.ar/ftp/cuadros/economia/cuadros_indices_patentamientos.xls")

    datos_excel = indec.get_patentamientos_excel(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )

    if datos_excel:
        print(f"✅ Excel descargado exitosamente")
        print(f"   Hojas encontradas: {len(datos_excel)}")

        # Procesar y guardar datos
        registros_guardados = 0
        db = next(get_db())

        for sheet_name, df in datos_excel.items():
            print(f"\n   📄 Procesando hoja: '{sheet_name}'")
            print(f"      Registros: {len(df)}")

            if len(df) > 0:
                # Identificar columnas de categorías de vehículos
                categorias = []
                for col in df.columns:
                    col_lower = str(col).lower()
                    if any(keyword in col_lower for keyword in ['auto', 'moto', 'camion', 'utilitario', 'total']):
                        categorias.append(col)

                if 'fecha' in df.columns and categorias:
                    # Insertar datos en la base de datos
                    for _, row in df.iterrows():
                        try:
                            fecha_dato = pd.to_datetime(row['fecha']).date()

                            for categoria in categorias:
                                valor = row.get(categoria)
                                if pd.notna(valor):
                                    # Insertar en tabla patentamientos
                                    query = text("""
                                        INSERT INTO patentamientos (
                                            fecha, categoria, cantidad, origen, provincia, fuente
                                        ) VALUES (
                                            :fecha, :categoria, :cantidad, 'TOTAL', 'NACIONAL', 'INDEC-Excel'
                                        )
                                        ON CONFLICT (fecha, categoria, origen, provincia)
                                        DO UPDATE SET
                                            cantidad = :cantidad,
                                            fuente = 'INDEC-Excel'
                                    """)

                                    db.execute(query, {
                                        'fecha': fecha_dato,
                                        'categoria': categoria,
                                        'cantidad': float(valor)
                                    })
                                    registros_guardados += 1

                        except Exception as e:
                            print(f"      ⚠️  Error procesando fila: {e}")
                            continue

                    db.commit()

        print(f"\n✅ INDEC Patentamientos completado")
        print(f"   Total guardado: {registros_guardados} registros")

    else:
        print("❌ No se pudo descargar el Excel de patentamientos")
        print("   Esto puede ocurrir si:")
        print("   - Estás ejecutando fuera de Argentina (geoblocking)")
        print("   - El servidor INDEC está temporalmente no disponible")
        print("   - Hay problemas de red/firewall")

except Exception as e:
    print(f"❌ ERROR en INDEC Patentamientos: {e}")

# ============================================================================
# 2. DNRPA - INSCRIPCIONES OFICIALES
# ============================================================================
print("\n" + "=" * 80)
print("📊 [2/3] DNRPA - INSCRIPCIONES OFICIALES")
print("=" * 80)

try:
    from backend.scrapers.dnrpa_scraper import DNRPAScraper

    dnrpa = DNRPAScraper()

    # Obtener datos del año en curso y año anterior
    anios = [fecha_hasta.year, fecha_hasta.year - 1]
    registros_dnrpa = 0

    for anio in anios:
        print(f"\n📥 Consultando DNRPA para año {anio}...")

        # Autos
        print(f"   Obteniendo datos de AUTOS...")
        datos_autos = dnrpa.get_provincias_summary(
            anio=anio,
            codigo_tipo='A',  # Autos
            codigo_tramite=3  # Inscripciones
        )

        if datos_autos:
            print(f"   ✅ {len(datos_autos)} registros de autos obtenidos")
            registros_dnrpa += len(datos_autos)
        else:
            print(f"   ⚠️  No se obtuvieron datos de autos para {anio}")

        # Motos
        print(f"   Obteniendo datos de MOTOS...")
        datos_motos = dnrpa.get_provincias_summary(
            anio=anio,
            codigo_tipo='M',  # Motos
            codigo_tramite=3
        )

        if datos_motos:
            print(f"   ✅ {len(datos_motos)} registros de motos obtenidos")
            registros_dnrpa += len(datos_motos)
        else:
            print(f"   ⚠️  No se obtuvieron datos de motos para {anio}")

    print(f"\n✅ DNRPA completado")
    print(f"   Total obtenido: {registros_dnrpa} registros")

except ImportError:
    print("⚠️  DNRPAScraper no disponible (requiere selenium)")
    print("   Instalar con: pip install selenium webdriver-manager")
except Exception as e:
    print(f"❌ ERROR en DNRPA: {e}")

# ============================================================================
# 3. IPI AUTOMOTRIZ - API INDEC
# ============================================================================
print("\n" + "=" * 80)
print("📊 [3/3] IPI AUTOMOTRIZ - Índice Producción Industrial")
print("=" * 80)

print("⚠️  ACTUALMENTE DESHABILITADO")
print("   El ID de serie de IPI Automotriz está desactualizado")
print("   ")
print("   📋 PARA HABILITAR:")
print("   1. Ir a: https://datos.gob.ar/dataset")
print("   2. Buscar: 'IPI automotriz' o 'producción industrial automotriz'")
print("   3. Copiar el ID de la serie (formato: XXX.X_XXXXXX_XXXX_X_XX)")
print("   4. Actualizar en: backend/api_clients/indec_client.py línea ~78")
print("   5. Descomentar la línea del ID")
print("   6. Volver a ejecutar este script")

# ============================================================================
# RESUMEN FINAL
# ============================================================================
print("\n" + "=" * 80)
print("📋 RESUMEN DE CARGA DE DATOS AUTOMOTRICES")
print("=" * 80)

db = next(get_db())

# Contar registros en la base de datos
try:
    result = db.execute(text("""
        SELECT
            fuente,
            COUNT(*) as cantidad,
            MIN(fecha) as fecha_min,
            MAX(fecha) as fecha_max
        FROM patentamientos
        GROUP BY fuente
    """))

    print("\n📊 DATOS EN BASE DE DATOS:")
    for row in result:
        print(f"   • {row.fuente}:")
        print(f"     - Registros: {row.cantidad}")
        print(f"     - Período: {row.fecha_min} a {row.fecha_max}")

except Exception as e:
    print(f"   No se pudo consultar la base de datos: {e}")

print("\n" + "=" * 80)
print("✅ PROCESO COMPLETADO")
print("=" * 80)

print("""
💡 PRÓXIMOS PASOS:

1. Verificar datos en dashboard Streamlit:
   streamlit run frontend/app.py

2. Si faltan datos automotrices:
   - Verificar conectividad desde Argentina
   - Buscar IDs correctos de series API en datos.gob.ar
   - Revisar logs de errores arriba

3. Fuentes adicionales a considerar:
   - ACARA (Asociación Concesionarios): Ventas concesionarios
   - ADEFA (Fábricas Automotores): Producción nacional
   - Cámaras provinciales automotrices
""")
