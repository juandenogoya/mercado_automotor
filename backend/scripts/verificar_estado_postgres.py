#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el estado de PostgreSQL y queries en ejecución
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings


def verificar_queries_activas():
    """Verifica qué queries están ejecutándose actualmente"""

    engine = create_engine(settings.get_database_url_sync())

    print("\n" + "="*80)
    print("🔍 VERIFICANDO ESTADO DE POSTGRESQL")
    print("="*80)

    query_activas = text("""
        SELECT
            pid,
            usename,
            application_name,
            state,
            query_start,
            NOW() - query_start as duration,
            LEFT(query, 100) as query_preview,
            wait_event_type,
            wait_event
        FROM pg_stat_activity
        WHERE state != 'idle'
        AND pid != pg_backend_pid()
        AND datname = current_database()
        ORDER BY query_start;
    """)

    try:
        with engine.connect() as conn:
            resultado = conn.execute(query_activas)
            filas = resultado.fetchall()

            if not filas:
                print("\n✅ No hay queries activas en este momento")
                print("   Esto podría significar que el proceso terminó o falló")
            else:
                print(f"\n📊 Queries Activas: {len(filas)}")
                print("="*80)

                for fila in filas:
                    print(f"\n🔹 PID: {fila[0]}")
                    print(f"   Usuario: {fila[1]}")
                    print(f"   Estado: {fila[3]}")
                    print(f"   Duración: {fila[5]}")
                    print(f"   Query: {fila[6]}...")
                    if fila[7]:
                        print(f"   ⏸️  Esperando: {fila[7]} - {fila[8]}")
                    else:
                        print(f"   ✅ Ejecutando activamente")

            # Verificar locks
            print("\n" + "="*80)
            print("🔒 VERIFICANDO LOCKS")
            print("="*80)

            query_locks = text("""
                SELECT
                    l.pid,
                    l.locktype,
                    l.mode,
                    l.granted,
                    a.query_start,
                    NOW() - a.query_start as duration,
                    LEFT(a.query, 80) as query_preview
                FROM pg_locks l
                LEFT JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE NOT l.granted
                AND a.datname = current_database();
            """)

            resultado_locks = conn.execute(query_locks)
            locks = resultado_locks.fetchall()

            if not locks:
                print("\n✅ No hay locks bloqueantes")
            else:
                print(f"\n⚠️  HAY {len(locks)} LOCKS BLOQUEANTES:")
                for lock in locks:
                    print(f"\n   PID: {lock[0]}")
                    print(f"   Tipo: {lock[1]}")
                    print(f"   Modo: {lock[2]}")
                    print(f"   Duración: {lock[5]}")
                    print(f"   Query: {lock[6]}...")

            # Verificar tamaño de las tablas base
            print("\n" + "="*80)
            print("📏 TAMAÑO DE TABLAS BASE")
            print("="*80)

            query_size = text("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows
                FROM pg_stat_user_tables
                WHERE tablename LIKE 'datos_gob%'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """)

            resultado_size = conn.execute(query_size)
            tablas = resultado_size.fetchall()

            print(f"\nTabla                              Tamaño      Filas")
            print("-" * 80)
            for tabla in tablas:
                print(f"{tabla[1]:<35} {tabla[2]:<12} {tabla[6]:,}")

    except Exception as e:
        print(f"\n❌ Error al verificar estado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verificar_queries_activas()
