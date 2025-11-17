#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar si las vistas materializadas KPIs existen
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings


def verificar_vistas():
    """Verifica si las vistas materializadas existen"""

    engine = create_engine(settings.get_database_url_sync())

    print("\n" + "="*80)
    print("🔍 VERIFICANDO VISTAS MATERIALIZADAS KPIs")
    print("="*80)

    query = text("""
        SELECT
            schemaname,
            matviewname as viewname,
            'materialized view' as type,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size
        FROM pg_matviews
        WHERE matviewname LIKE 'kpi_%'

        UNION ALL

        SELECT
            schemaname,
            tablename as viewname,
            'table' as type,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables
        WHERE tablename LIKE 'kpi_%' OR tablename LIKE 'ml_features%'

        ORDER BY viewname;
    """)

    try:
        with engine.connect() as conn:
            resultado = conn.execute(query)
            vistas = resultado.fetchall()

            if not vistas:
                print("\n❌ No se encontraron vistas materializadas KPIs")
                print("\nPosibles causas:")
                print("   1. Las vistas no se crearon correctamente")
                print("   2. Las queries se cancelaron antes de hacer commit")
                print("   3. Se crearon en otro esquema")
            else:
                print(f"\n✅ Encontradas {len(vistas)} vistas/tablas KPIs:")
                print("="*80)
                print(f"{'Esquema':<15} {'Nombre':<40} {'Tipo':<20} {'Tamaño':<15}")
                print("-"*80)
                for vista in vistas:
                    print(f"{vista[0]:<15} {vista[1]:<40} {vista[2]:<20} {vista[3]:<15}")

                # Verificar función
                print("\n" + "="*80)
                print("🔧 VERIFICANDO FUNCIÓN REFRESH")
                print("="*80)

                query_funcion = text("""
                    SELECT
                        n.nspname as schema,
                        p.proname as function_name,
                        pg_get_function_arguments(p.oid) as arguments
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE p.proname LIKE '%refresh_kpi%';
                """)

                resultado_func = conn.execute(query_funcion)
                funciones = resultado_func.fetchall()

                if funciones:
                    print(f"\n✅ Encontradas {len(funciones)} funciones refresh:")
                    for func in funciones:
                        print(f"   {func[0]}.{func[1]}({func[2]})")
                else:
                    print("\n❌ No se encontró función refresh_kpis_materializados()")

                # Contar registros
                print("\n" + "="*80)
                print("📊 ESTADÍSTICAS DE REGISTROS")
                print("="*80)

                for vista in vistas:
                    if vista[2] == 'materialized view' or vista[2] == 'table':
                        try:
                            query_count = text(f"SELECT COUNT(*) FROM {vista[0]}.{vista[1]}")
                            count_result = conn.execute(query_count)
                            count = count_result.scalar()
                            print(f"\n{vista[1]}: {count:,} registros")
                        except Exception as e:
                            print(f"\n{vista[1]}: Error al contar - {e}")

    except Exception as e:
        print(f"\n❌ Error al verificar vistas: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    verificar_vistas()
