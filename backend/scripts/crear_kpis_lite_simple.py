#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplificado para crear KPIs LITE
Ejecuta todo el SQL de una vez sin dividir en bloques
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import time
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings


def crear_kpis_lite_simple():
    """Ejecuta el script SQL LITE completo sin dividir en bloques"""

    print("\n" + "="*80)
    print("🚀 CREANDO KPIs LITE - VERSIÓN SIMPLIFICADA")
    print("="*80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Parsear DB info
    db_url = str(settings.database_url)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        db_name = parsed.path.lstrip('/')
        db_host = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
    except:
        db_name = "PostgreSQL"
        db_host = "localhost"

    print(f"🔗 Base de datos: {db_name}")
    print(f"🖥️  Host: {db_host}")

    print("\n📋 Se crearán:")
    print("   - 4 vistas materializadas (Segmentación, Financiamiento, Antigüedad, Demanda)")
    print("   - Índices para optimizar consultas")
    print("   - Función refresh_kpis_lite()")

    print("\n⏱️  Tiempo estimado: 5-10 minutos")
    print("⚠️  NO interrumpir el proceso")

    respuesta = input("\n¿Continuar? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Cancelado")
        return False

    # Leer SQL
    sql_file = Path(__file__).parent.parent / "sql" / "crear_kpis_lite.sql"

    if not sql_file.exists():
        print(f"\n❌ Error: No se encontró {sql_file}")
        return False

    print("\n📄 Leyendo SQL...")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Crear engine
    engine = create_engine(settings.get_database_url_sync())

    print("\n🚀 Ejecutando SQL completo...")
    print("   (Puede tardar 5-10 minutos, espera sin interrumpir)")

    inicio = time.time()

    try:
        # Ejecutar TODO el SQL en una sola transacción
        # Esto es más seguro que dividir en bloques
        with engine.begin() as conn:
            conn.execute(text(sql_content))

        duracion = time.time() - inicio

        print(f"\n{'='*80}")
        print("✅ KPIs LITE CREADOS EXITOSAMENTE")
        print(f"{'='*80}")
        print(f"⏱️  Tiempo total: {duracion:.1f}s ({duracion/60:.1f} minutos)")

        print("\n📊 Vistas creadas:")
        print("   ✓ kpi_segmentacion_demografica_lite")
        print("   ✓ kpi_financiamiento_lite")
        print("   ✓ kpi_antiguedad_vehiculos_lite")
        print("   ✓ kpi_demanda_activa_lite")

        print("\n🔧 Función creada:")
        print("   ✓ refresh_kpis_lite(modo)")

        print("\n🚀 Próximos pasos:")
        print("   1. Verificar: python backend/scripts/verificar_vistas_kpis.py")
        print("   2. Dashboard: streamlit run frontend/app_datos_gob.py")
        print("   3. Actualizar KPIs: SELECT refresh_kpis_lite('CONCURRENT');")

        print(f"\n{'='*80}\n")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    crear_kpis_lite_simple()
