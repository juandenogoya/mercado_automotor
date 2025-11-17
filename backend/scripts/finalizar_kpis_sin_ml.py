#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para finalizar KPIs creando solo la función refresh
(sin crear la tabla ML que es muy pesada)

Usa este script después de cancelar la creación de KPIs completos
cuando la tabla ML se quedó bloqueada.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings


def finalizar_kpis():
    """Crea solo la función refresh_kpis_materializados"""

    print("\n" + "="*80)
    print("🔧 FINALIZANDO KPIs - CREANDO FUNCIÓN REFRESH")
    print("="*80)

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

    print(f"\n🔗 Base de datos: {db_name}")
    print(f"🖥️  Host: {db_host}")

    print("\n📋 Estado actual:")
    print("   ✅ kpi_segmentacion_demografica (ya creada)")
    print("   ✅ kpi_financiamiento_segmento (ya creada)")
    print("   ✅ kpi_antiguedad_vehiculos (ya creada)")
    print("   ✅ kpi_demanda_activa (ya creada)")
    print("   ⏭️  ml_features_propension_compra (se omitirá, muy pesada)")
    print("   ❓ refresh_kpis_materializados() (función a crear)")

    print("\n💡 La función refresh permitirá actualizar los KPIs cuando")
    print("   haya nuevos datos, sin recrearlos desde cero.")

    respuesta = input("\n¿Deseas continuar y crear la función? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Operación cancelada")
        return False

    # Leer SQL
    sql_file = Path(__file__).parent.parent / "sql" / "crear_funcion_refresh.sql"

    if not sql_file.exists():
        print(f"\n❌ Error: No se encontró el archivo {sql_file}")
        return False

    print("\n📄 Leyendo SQL...")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Ejecutar
    print("🚀 Creando función refresh_kpis_materializados()...")

    engine = create_engine(settings.get_database_url_sync())

    try:
        with engine.begin() as conn:
            conn.execute(text(sql_content))

        print("\n" + "="*80)
        print("✅ FUNCIÓN CREADA EXITOSAMENTE")
        print("="*80)

        print("\n🎉 ¡KPIs completos configurados correctamente!")

        print("\n📊 Vistas materializadas disponibles:")
        print("   ✓ kpi_segmentacion_demografica")
        print("   ✓ kpi_financiamiento_segmento")
        print("   ✓ kpi_antiguedad_vehiculos")
        print("   ✓ kpi_demanda_activa")

        print("\n🔧 Función disponible:")
        print("   ✓ refresh_kpis_materializados(modo)")

        print("\n💡 Uso de la función refresh:")
        print("   -- Modo CONCURRENT (no bloquea lecturas)")
        print("   SELECT refresh_kpis_materializados('CONCURRENT');")
        print()
        print("   -- Modo FULL (más rápido pero bloquea)")
        print("   SELECT refresh_kpis_materializados('FULL');")

        print("\n📝 Nota sobre la tabla ML:")
        print("   La tabla ml_features_propension_compra se puede crear después")
        print("   por separado cuando tengas tiempo (puede tardar 2-3 horas):")
        print("   python backend/ml/preparar_datos_propension.py --crear-tabla-features")

        print("\n🚀 Próximos pasos:")
        print("   1. Verificar KPIs: python backend/scripts/actualizar_kpis.py --stats")
        print("   2. Usar dashboard: streamlit run frontend/app_datos_gob.py")
        print("   3. Entrenar ML cuando quieras (opcional)")

        print("="*80 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Error al crear función: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    finalizar_kpis()
