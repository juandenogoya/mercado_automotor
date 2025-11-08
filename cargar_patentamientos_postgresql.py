"""
Script para cargar datos de patentamientos desde Excel a PostgreSQL
Lee checkpoint_provincial_2020_2025.xlsx y carga a la base de datos

EJECUCIÓN:
python cargar_patentamientos_postgresql.py
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent))

from backend.config.settings import settings

print("=" * 80)
print("📊 CARGA DE PATENTAMIENTOS A POSTGRESQL")
print("=" * 80)
print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Ruta del archivo Excel
excel_path = Path(__file__).parent / "checkpoint_provincial_2020_2025.xlsx"

if not excel_path.exists():
    print(f"\n❌ ERROR: No se encontró el archivo {excel_path}")
    print("   Ejecuta primero el scraping provincial histórico")
    sys.exit(1)

print(f"\n📥 Leyendo archivo Excel: {excel_path}")

try:
    df = pd.read_excel(excel_path)
    print(f"✅ {len(df)} registros leídos")
    print(f"📋 Columnas: {list(df.columns)}")

    # Verificar columnas esperadas
    required_cols = ['Provincia / Mes', 'anio', 'Total', 'tipo_vehiculo']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        print(f"\n⚠️ Advertencia: Faltan columnas: {missing_cols}")

except Exception as e:
    print(f"\n❌ ERROR leyendo Excel: {e}")
    sys.exit(1)

# Conectar a PostgreSQL
print(f"\n🔌 Conectando a PostgreSQL...")

try:
    engine = create_engine(settings.get_database_url_sync())
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    print("✅ Conexión exitosa")

except Exception as e:
    print(f"\n❌ ERROR conectando a PostgreSQL: {e}")
    print("\n💡 Verifica:")
    print("   1. PostgreSQL está corriendo")
    print("   2. Las credenciales en .env son correctas")
    print("   3. La base de datos existe")
    sys.exit(1)

# Crear tabla si no existe
print(f"\n📋 Creando tabla si no existe...")

create_table_sql = """
CREATE TABLE IF NOT EXISTS patentamientos_provincial (
    id SERIAL PRIMARY KEY,
    provincia VARCHAR(100) NOT NULL,
    anio INTEGER NOT NULL,
    mes VARCHAR(10),
    cantidad INTEGER DEFAULT 0,
    tipo_vehiculo VARCHAR(20) DEFAULT 'Autos',
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provincia, anio, mes, tipo_vehiculo)
);

CREATE INDEX IF NOT EXISTS idx_paten_prov_provincia ON patentamientos_provincial(provincia);
CREATE INDEX IF NOT EXISTS idx_paten_prov_anio ON patentamientos_provincial(anio);
CREATE INDEX IF NOT EXISTS idx_paten_prov_tipo ON patentamientos_provincial(tipo_vehiculo);
"""

try:
    db.execute(text(create_table_sql))
    db.commit()
    print("✅ Tabla creada/verificada")

except Exception as e:
    print(f"❌ ERROR creando tabla: {e}")
    db.rollback()
    sys.exit(1)

# Transformar datos para carga
print(f"\n🔄 Transformando datos...")

# Meses a procesar
meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

registros_cargados = 0
registros_actualizados = 0
errores = 0

print(f"\n📤 Cargando datos a PostgreSQL...")

try:
    for idx, row in df.iterrows():
        provincia = row.get('Provincia / Mes', 'DESCONOCIDA')
        anio = int(row.get('anio', 0))
        tipo_vehiculo = row.get('tipo_vehiculo', 'Autos')

        # Procesar cada mes
        for mes_nombre in meses:
            if mes_nombre in df.columns:
                cantidad = row.get(mes_nombre, 0)

                # Convertir a int si es posible
                try:
                    cantidad = int(cantidad) if pd.notna(cantidad) else 0
                except (ValueError, TypeError):
                    cantidad = 0

                # Insert or update
                insert_sql = text("""
                    INSERT INTO patentamientos_provincial
                        (provincia, anio, mes, cantidad, tipo_vehiculo, fecha_carga)
                    VALUES
                        (:provincia, :anio, :mes, :cantidad, :tipo_vehiculo, :fecha_carga)
                    ON CONFLICT (provincia, anio, mes, tipo_vehiculo)
                    DO UPDATE SET
                        cantidad = EXCLUDED.cantidad,
                        fecha_carga = EXCLUDED.fecha_carga
                """)

                try:
                    result = db.execute(insert_sql, {
                        'provincia': provincia,
                        'anio': anio,
                        'mes': mes_nombre,
                        'cantidad': cantidad,
                        'tipo_vehiculo': tipo_vehiculo,
                        'fecha_carga': datetime.now()
                    })

                    if result.rowcount > 0:
                        registros_cargados += 1
                    else:
                        registros_actualizados += 1

                except Exception as e:
                    errores += 1
                    print(f"   ❌ Error en {provincia} {anio} {mes_nombre}: {e}")

        # Commit cada 10 provincias
        if (idx + 1) % 10 == 0:
            db.commit()
            print(f"   💾 Checkpoint: {idx + 1}/{len(df)} provincias procesadas")

    # Commit final
    db.commit()
    print(f"\n✅ Carga completada")

except Exception as e:
    print(f"\n❌ ERROR durante la carga: {e}")
    db.rollback()
    sys.exit(1)

# Verificar datos cargados
print(f"\n📊 Verificando datos en PostgreSQL...")

try:
    count_sql = text("SELECT COUNT(*) as total FROM patentamientos_provincial")
    result = db.execute(count_sql)
    total_bd = result.fetchone()[0]

    print(f"✅ Total de registros en BD: {total_bd:,}")

    # Estadísticas por año
    stats_sql = text("""
        SELECT anio, COUNT(*) as registros, SUM(cantidad) as total_patentamientos
        FROM patentamientos_provincial
        GROUP BY anio
        ORDER BY anio
    """)

    result = db.execute(stats_sql)
    print(f"\n📈 ESTADÍSTICAS POR AÑO:")
    print("-" * 80)
    for row in result:
        print(f"  {row.anio}: {row.registros:>4} registros | {row.total_patentamientos:>10,} patentamientos")

    # Top 5 provincias
    top_sql = text("""
        SELECT provincia, SUM(cantidad) as total
        FROM patentamientos_provincial
        GROUP BY provincia
        ORDER BY total DESC
        LIMIT 5
    """)

    result = db.execute(top_sql)
    print(f"\n🏆 TOP 5 PROVINCIAS (Total histórico):")
    print("-" * 80)
    for idx, row in enumerate(result, 1):
        print(f"  {idx}. {row.provincia}: {row.total:,}")

except Exception as e:
    print(f"❌ ERROR verificando datos: {e}")

finally:
    db.close()

# Resumen final
print("\n" + "=" * 80)
print("✅ PROCESO COMPLETADO")
print("=" * 80)
print(f"📊 Registros nuevos:      {registros_cargados:,}")
print(f"🔄 Registros actualizados: {registros_actualizados:,}")
print(f"❌ Errores:                {errores}")
print(f"💾 Total en BD:            {total_bd:,}")
print("=" * 80)

print(f"\n🎯 Próximos pasos:")
print("  1. Actualizar dashboard para leer de PostgreSQL")
print("  2. Cargar datos de seccionales si están disponibles")
print("  3. Verificar datos en el dashboard: streamlit run frontend/app.py")
print("=" * 80)
