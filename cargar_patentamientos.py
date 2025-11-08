"""
🚗 MÓDULO PATENTAMIENTOS - Script de Carga de Datos

Fuentes:
1. DNRPA - Dirección Nacional del Registro de la Propiedad Automotor (Scraping)
2. INDEC - Patentamientos desde Excel (Datos históricos)

USO:
    python cargar_patentamientos.py

AUTOR: Sistema de Inteligencia Comercial Automotor
"""
from datetime import date, datetime
from backend.scrapers.dnrpa_scraper import DNRPAScraper
from backend.api_clients.indec_client import INDECClient
from backend.utils.database import get_db, SessionLocal
from backend.models.patentamientos import Patentamiento
from sqlalchemy import text
import pandas as pd

print("=" * 80)
print("🚗 MÓDULO PATENTAMIENTOS - Carga de Datos")
print("=" * 80)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
anio_actual = date.today().year
anio_anterior = anio_actual - 1

print(f"\n⚙️  CONFIGURACIÓN:")
print(f"   Años a procesar: {anio_anterior}, {anio_actual}")
print(f"   Fuentes: DNRPA (scraping) + INDEC (Excel)")
print(f"   Base de datos: PostgreSQL (tabla: patentamientos)")

# ============================================================================
# PARTE 1: DNRPA - INSCRIPCIONES OFICIALES (SCRAPING)
# ============================================================================
print("\n" + "=" * 80)
print("📊 [1/2] DNRPA - Inscripciones Oficiales (Scraping)")
print("=" * 80)

total_registros_dnrpa = 0

try:
    dnrpa = DNRPAScraper()

    # Procesar ambos años
    for anio in [anio_anterior, anio_actual]:
        print(f"\n📅 Procesando año: {anio}")
        print("-" * 80)

        # ========== AUTOS ==========
        print(f"\n🚗 Obteniendo datos de AUTOS...")

        df_autos = dnrpa.get_provincias_summary(
            anio=anio,
            codigo_tipo='A',  # Autos
            codigo_tramite=3  # Inscripciones
        )

        if df_autos is not None and not df_autos.empty:
            print(f"   ✅ Datos obtenidos: {len(df_autos)} provincias")
            print(f"   📋 Columnas del DataFrame: {list(df_autos.columns)}")
            print(f"   📊 Muestra de datos:")
            print(df_autos.head())

            # Usar context manager para la sesión
            with get_db() as db:
                # Convertir DataFrame a registros en BD
                for _, row in df_autos.iterrows():
                    provincia = row.get('provincia', 'DESCONOCIDA')

                    # Procesar cada mes
                    for mes in range(1, 13):
                        mes_col = f'mes_{mes}'
                        cantidad = row.get(mes_col, 0)

                        if pd.notna(cantidad) and cantidad > 0:
                            try:
                                # Insertar en BD
                                query = text("""
                                    INSERT INTO patentamientos (
                                        fecha, anio, mes, tipo_vehiculo, marca, modelo,
                                        segmento, provincia, cantidad, fuente, periodo_reportado
                                    ) VALUES (
                                        :fecha, :anio, :mes, :tipo_vehiculo, :marca, :modelo,
                                        :segmento, :provincia, :cantidad, :fuente, :periodo_reportado
                                    )
                                    ON CONFLICT DO NOTHING
                                """)

                                db.execute(query, {
                                    'fecha': date(anio, mes, 1),
                                    'anio': anio,
                                    'mes': mes,
                                    'tipo_vehiculo': 'Autos',
                                    'marca': None,
                                    'modelo': None,
                                    'segmento': None,
                                    'provincia': provincia,
                                    'cantidad': int(cantidad),
                                    'fuente': 'DNRPA',
                                    'periodo_reportado': f'{anio}-{mes:02d}'
                                })

                                total_registros_dnrpa += 1

                            except Exception as e:
                                print(f"      ⚠️  Error insertando: {e}")
                                continue

            print(f"   💾 Guardados en base de datos")
        else:
            print(f"   ⚠️  No se obtuvieron datos de autos para {anio}")

        # ========== MOTOS ==========
        print(f"\n🏍️  Obteniendo datos de MOTOS...")

        df_motos = dnrpa.get_provincias_summary(
            anio=anio,
            codigo_tipo='M',  # Motos
            codigo_tramite=3
        )

        if df_motos is not None and not df_motos.empty:
            print(f"   ✅ Datos obtenidos: {len(df_motos)} provincias")

            with get_db() as db:
                for _, row in df_motos.iterrows():
                    provincia = row.get('provincia', 'DESCONOCIDA')

                    for mes in range(1, 13):
                        mes_col = f'mes_{mes}'
                        cantidad = row.get(mes_col, 0)

                        if pd.notna(cantidad) and cantidad > 0:
                            try:
                                query = text("""
                                    INSERT INTO patentamientos (
                                        fecha, anio, mes, tipo_vehiculo, marca, modelo,
                                        segmento, provincia, cantidad, fuente, periodo_reportado
                                    ) VALUES (
                                        :fecha, :anio, :mes, :tipo_vehiculo, :marca, :modelo,
                                        :segmento, :provincia, :cantidad, :fuente, :periodo_reportado
                                    )
                                    ON CONFLICT DO NOTHING
                                """)

                                db.execute(query, {
                                    'fecha': date(anio, mes, 1),
                                    'anio': anio,
                                    'mes': mes,
                                    'tipo_vehiculo': 'Motos',
                                    'marca': None,
                                    'modelo': None,
                                    'segmento': None,
                                    'provincia': provincia,
                                    'cantidad': int(cantidad),
                                    'fuente': 'DNRPA',
                                    'periodo_reportado': f'{anio}-{mes:02d}'
                                })

                                total_registros_dnrpa += 1

                            except Exception as e:
                                continue

            print(f"   💾 Guardados en base de datos")
        else:
            print(f"   ⚠️  No se obtuvieron datos de motos para {anio}")

    print(f"\n✅ DNRPA completado")
    print(f"   Total guardado: {total_registros_dnrpa} registros")

except Exception as e:
    print(f"\n❌ ERROR en DNRPA: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# PARTE 2: INDEC - PATENTAMIENTOS EXCEL
# ============================================================================
print("\n" + "=" * 80)
print("📊 [2/2] INDEC - Patentamientos desde Excel")
print("=" * 80)

total_registros_indec = 0

try:
    indec = INDECClient()

    print(f"\n📥 Descargando Excel de patentamientos...")
    print(f"   URL: https://www.indec.gob.ar/ftp/cuadros/economia/cuadros_indices_patentamientos.xls")

    # Obtener últimos 24 meses
    fecha_desde = date(anio_anterior, 1, 1)
    fecha_hasta = date.today()

    datos_excel = indec.get_patentamientos_excel(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )

    if datos_excel:
        print(f"✅ Excel descargado exitosamente")
        print(f"   Hojas encontradas: {len(datos_excel)}")

        for sheet_name, df in datos_excel.items():
            print(f"\n   📄 Procesando hoja: '{sheet_name}'")
            print(f"      Registros: {len(df)}")

            if len(df) > 0 and 'fecha' in df.columns:
                with get_db() as db:
                    # Guardar en BD
                    for _, row in df.iterrows():
                        try:
                            fecha_dato = pd.to_datetime(row['fecha']).date()

                            # Buscar columnas de cantidad
                            for col in df.columns:
                                if col != 'fecha' and col != 'Período' and col != 'Periodo':
                                    valor = row.get(col)

                                    if pd.notna(valor) and valor != '':
                                        query = text("""
                                            INSERT INTO patentamientos (
                                                fecha, anio, mes, tipo_vehiculo, marca, modelo,
                                                segmento, provincia, cantidad, fuente, periodo_reportado
                                            ) VALUES (
                                                :fecha, :anio, :mes, :tipo_vehiculo, :marca, :modelo,
                                                :segmento, :provincia, :cantidad, :fuente, :periodo_reportado
                                            )
                                            ON CONFLICT DO NOTHING
                                        """)

                                        db.execute(query, {
                                            'fecha': fecha_dato,
                                            'anio': fecha_dato.year,
                                            'mes': fecha_dato.month,
                                            'tipo_vehiculo': col,
                                            'marca': None,
                                            'modelo': None,
                                            'segmento': sheet_name,
                                            'provincia': 'NACIONAL',
                                            'cantidad': int(float(valor)) if str(valor).replace('.','').isdigit() else 0,
                                            'fuente': 'INDEC-Excel',
                                            'periodo_reportado': fecha_dato.strftime('%Y-%m')
                                        })

                                        total_registros_indec += 1

                        except Exception as e:
                            print(f"      ⚠️  Error en fila: {e}")
                            continue

                print(f"      💾 Guardados")

        print(f"\n✅ INDEC completado")
        print(f"   Total guardado: {total_registros_indec} registros")
    else:
        print(f"\n⚠️  No se pudo descargar el Excel de INDEC")
        print(f"   Esto puede ocurrir si estás fuera de Argentina (geoblocking)")

except Exception as e:
    print(f"\n❌ ERROR en INDEC: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# RESUMEN FINAL
# ============================================================================
print("\n" + "=" * 80)
print("📋 RESUMEN FINAL - MÓDULO PATENTAMIENTOS")
print("=" * 80)

try:
    # Crear nueva sesión para consultas
    db_session = SessionLocal()

    # Consultar totales en BD
    result = db_session.execute(text("""
        SELECT
            fuente,
            tipo_vehiculo,
            COUNT(*) as cantidad,
            SUM(cantidad) as total_patentamientos,
            MIN(fecha) as fecha_min,
            MAX(fecha) as fecha_max
        FROM patentamientos
        GROUP BY fuente, tipo_vehiculo
        ORDER BY fuente, tipo_vehiculo
    """)).fetchall()

    if result:
        print("\n📊 DATOS EN BASE DE DATOS:")
        for row in result:
            print(f"\n   • {row.fuente} - {row.tipo_vehiculo}:")
            print(f"     Registros: {row.cantidad}")
            print(f"     Total patentamientos: {row.total_patentamientos:,}")
            print(f"     Período: {row.fecha_min} a {row.fecha_max}")

    # Total general
    total_general = db_session.execute(text("""
        SELECT COUNT(*) as total FROM patentamientos
    """)).fetchone()

    print(f"\n{'=' * 80}")
    print(f"✅ TOTAL EN BASE DE DATOS: {total_general.total} registros")
    print(f"{'=' * 80}")

    db_session.close()

except Exception as e:
    print(f"   ⚠️  Error consultando BD: {e}")
    import traceback
    traceback.print_exc()

print("""
💡 PRÓXIMOS PASOS:

1. Verificar datos en el dashboard:
   streamlit run frontend/app.py

2. Los datos están guardados en la tabla 'patentamientos' con:
   - Fuente: 'DNRPA' (datos oficiales por provincia)
   - Fuente: 'INDEC-Excel' (índices históricos)

3. Vamos a actualizar el dashboard para mostrar estos datos
   con gráficos de evolución temporal y comparaciones.
""")

print("=" * 80)
print("🚗 MÓDULO PATENTAMIENTOS FINALIZADO")
print("=" * 80)
