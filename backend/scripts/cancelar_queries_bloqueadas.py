#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para cancelar queries bloqueadas en PostgreSQL
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings


def cancelar_queries_bloqueadas():
    """Cancela todas las queries bloqueadas o de larga duración"""

    engine = create_engine(settings.get_database_url_sync())

    print("\n" + "="*80)
    print("🛑 CANCELANDO QUERIES BLOQUEADAS")
    print("="*80)

    # Primero, mostrar queries activas
    query_activas = text("""
        SELECT
            pid,
            usename,
            application_name,
            state,
            query_start,
            NOW() - query_start as duration,
            LEFT(query, 80) as query_preview
        FROM pg_stat_activity
        WHERE state != 'idle'
        AND pid != pg_backend_pid()
        AND datname = current_database()
        ORDER BY query_start;
    """)

    try:
        with engine.connect() as conn:
            resultado = conn.execute(query_activas)
            queries = resultado.fetchall()

            if not queries:
                print("\n✅ No hay queries activas para cancelar")
                return

            print(f"\n📊 Encontradas {len(queries)} queries activas:")
            print("="*80)

            pids_a_cancelar = []
            for q in queries:
                print(f"\n🔹 PID: {q[0]}")
                print(f"   Usuario: {q[1]}")
                print(f"   Estado: {q[3]}")
                print(f"   Duración: {q[5]}")
                print(f"   Query: {q[6]}...")

                # Agregar a lista de PIDs a cancelar si:
                # - Lleva más de 1 minuto
                # - O contiene "CREATE MATERIALIZED VIEW"
                duracion_str = str(q[5])
                query_text = q[6] or ""

                if ":" in duracion_str:  # Tiene horas o más de 1 minuto
                    pids_a_cancelar.append(q[0])
                elif "CREATE MATERIALIZED VIEW" in query_text.upper():
                    pids_a_cancelar.append(q[0])

            if not pids_a_cancelar:
                print("\n✅ No hay queries que necesiten cancelarse")
                return

            print("\n" + "="*80)
            print(f"⚠️  Se cancelarán {len(pids_a_cancelar)} queries")
            print("="*80)

            respuesta = input("\n¿Confirmas cancelar estas queries? (s/n): ")

            if respuesta.lower() == 's':
                print("\n🛑 Cancelando queries...")

                for pid in pids_a_cancelar:
                    try:
                        # Intentar cancelar primero (más suave)
                        cancel_query = text(f"SELECT pg_cancel_backend({pid})")
                        resultado = conn.execute(cancel_query)
                        cancelado = resultado.scalar()

                        if cancelado:
                            print(f"   ✓ Query {pid} cancelada exitosamente")
                        else:
                            # Si no se pudo cancelar, terminar el proceso (más fuerte)
                            print(f"   ⚠️  No se pudo cancelar {pid}, intentando terminar proceso...")
                            terminate_query = text(f"SELECT pg_terminate_backend({pid})")
                            resultado = conn.execute(terminate_query)
                            terminado = resultado.scalar()

                            if terminado:
                                print(f"   ✓ Proceso {pid} terminado exitosamente")
                            else:
                                print(f"   ❌ No se pudo terminar proceso {pid}")

                    except Exception as e:
                        print(f"   ❌ Error al cancelar {pid}: {e}")

                print("\n✅ Proceso de cancelación completado")
                print("\n💡 Ahora puedes ejecutar el script de KPIs nuevamente")

            else:
                print("\n❌ Cancelación abortada por el usuario")

    except Exception as e:
        print(f"\n❌ Error al cancelar queries: {e}")
        import traceback
        traceback.print_exc()


def limpiar_locks():
    """Limpia locks huérfanos en PostgreSQL"""

    engine = create_engine(settings.get_database_url_sync())

    print("\n" + "="*80)
    print("🧹 LIMPIANDO LOCKS")
    print("="*80)

    query_locks = text("""
        SELECT
            l.pid,
            l.locktype,
            l.mode,
            l.granted
        FROM pg_locks l
        LEFT JOIN pg_stat_activity a ON l.pid = a.pid
        WHERE NOT l.granted
        AND (a.pid IS NULL OR a.state = 'idle');
    """)

    try:
        with engine.connect() as conn:
            resultado = conn.execute(query_locks)
            locks = resultado.fetchall()

            if not locks:
                print("\n✅ No hay locks huérfanos para limpiar")
            else:
                print(f"\n⚠️  Encontrados {len(locks)} locks huérfanos")
                for lock in locks:
                    print(f"   PID: {lock[0]}, Tipo: {lock[1]}, Modo: {lock[2]}")

    except Exception as e:
        print(f"\n❌ Error al verificar locks: {e}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔧 HERRAMIENTA DE LIMPIEZA DE POSTGRESQL")
    print("="*80)

    cancelar_queries_bloqueadas()
    limpiar_locks()

    print("\n" + "="*80)
    print("✅ LIMPIEZA COMPLETADA")
    print("="*80)
    print("\n💡 Recomendaciones:")
    print("   1. Ejecuta solo UNA vez el script de KPIs")
    print("   2. Espera pacientemente (puede tardar 20-40 min)")
    print("   3. Usa la versión LITE si quieres algo más rápido")
    print("\n")
