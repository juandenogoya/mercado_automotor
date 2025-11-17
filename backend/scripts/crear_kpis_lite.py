#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear KPIs LITE (versión rápida con menos dimensiones)

Esta versión es 5-10x más rápida que la completa porque:
- Solo usa dimensiones principales: provincia, marca, año, mes
- Omite: localidad, género, edad granular, tipo_persona, etc.
- Ideal para testing o PCs con recursos limitados

Tiempo estimado: 5-10 minutos con 13M registros
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import time
from datetime import datetime

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings


def crear_kpis_lite():
    """Ejecuta el script SQL de KPIs LITE"""

    print("\n" + "="*80)
    print("🚀 CREANDO KPIs MATERIALIZADOS - VERSIÓN LITE")
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

    print("\n" + "="*80)
    print("📊 VERSIÓN LITE - Características:")
    print("="*80)
    print("✓ Dimensiones: provincia, marca, año, mes")
    print("✓ KPIs: Segmentación, Financiamiento, Antigüedad, Demanda Activa")
    print("✓ Tiempo estimado: 5-10 minutos (con 13M registros)")
    print("✓ Uso de RAM: ~2-4 GB")
    print("\n⚠️  IMPORTANTE: No interrumpir el proceso una vez iniciado")
    print("="*80)

    # Confirmar
    respuesta = input("\n¿Deseas continuar? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Operación cancelada")
        return False

    # Leer archivo SQL
    sql_file = Path(__file__).parent.parent / "sql" / "crear_kpis_lite.sql"

    if not sql_file.exists():
        print(f"\n❌ Error: No se encontró el archivo {sql_file}")
        return False

    print("\n📄 Leyendo archivo SQL...")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Dividir en bloques para mostrar progreso
    bloques = []
    bloque_actual = []

    for linea in sql_content.split('\n'):
        bloque_actual.append(linea)

        # Detectar fin de bloque
        if any([
            'DROP MATERIALIZED VIEW IF EXISTS' in linea.upper(),
            linea.strip().endswith(';') and 'CREATE MATERIALIZED VIEW' in '\n'.join(bloque_actual).upper(),
            linea.strip().endswith(';') and 'CREATE UNIQUE INDEX' in '\n'.join(bloque_actual).upper(),
            linea.strip().endswith(';') and 'CREATE INDEX' in '\n'.join(bloque_actual).upper(),
            linea.strip().endswith('$$;') and 'CREATE OR REPLACE FUNCTION' in '\n'.join(bloque_actual).upper(),
        ]):
            if bloque_actual:
                bloques.append('\n'.join(bloque_actual))
                bloque_actual = []

    if bloque_actual:
        bloques.append('\n'.join(bloque_actual))

    print(f"\n⏳ Procesando {len(bloques)} bloques SQL...")
    print("="*80)

    # Crear engine
    engine = create_engine(settings.get_database_url_sync())

    inicio_total = time.time()

    try:
        with engine.begin() as conn:  # Usar begin() para commit automático
            for i, bloque in enumerate(bloques, 1):
                bloque_limpio = bloque.strip()
                if not bloque_limpio or bloque_limpio.startswith('--'):
                    continue

                # Identificar qué se está ejecutando
                if 'DROP' in bloque_limpio.upper():
                    print(f"\n[{i}/{len(bloques)}] 🗑️  Limpiando vistas existentes...")
                elif 'CREATE MATERIALIZED VIEW kpi_segmentacion_demografica_lite' in bloque_limpio:
                    print(f"\n[{i}/{len(bloques)}] 📊 Creando: kpi_segmentacion_demografica_lite")
                    print(f"     Dimensiones: provincia × marca × año × mes")
                    print(f"     ⏳ Puede tardar 2-4 minutos...")
                elif 'CREATE MATERIALIZED VIEW kpi_financiamiento_lite' in bloque_limpio:
                    print(f"\n[{i}/{len(bloques)}] 💰 Creando: kpi_financiamiento_lite")
                    print(f"     Cálculo: IF por provincia y marca")
                    print(f"     ⏳ Puede tardar 2-3 minutos...")
                elif 'CREATE MATERIALIZED VIEW kpi_antiguedad_vehiculos_lite' in bloque_limpio:
                    print(f"\n[{i}/{len(bloques)}] 🚗 Creando: kpi_antiguedad_vehiculos_lite")
                    print(f"     Cálculo: EVT e IAM")
                    print(f"     ⏳ Puede tardar 2-4 minutos...")
                elif 'CREATE MATERIALIZED VIEW kpi_demanda_activa_lite' in bloque_limpio:
                    print(f"\n[{i}/{len(bloques)}] 📈 Creando: kpi_demanda_activa_lite")
                    print(f"     Cálculo: IDA por provincia y marca")
                    print(f"     ⏳ Puede tardar 1-2 minutos...")
                elif 'CREATE OR REPLACE FUNCTION refresh_kpis_lite' in bloque_limpio:
                    print(f"\n[{i}/{len(bloques)}] 🔧 Creando función: refresh_kpis_lite()")
                elif 'CREATE UNIQUE INDEX' in bloque_limpio.upper():
                    print(f"\n[{i}/{len(bloques)}] 🔑 Creando índices únicos...")
                elif 'CREATE INDEX' in bloque_limpio.upper():
                    print(f"\n[{i}/{len(bloques)}] 🔍 Creando índices...")
                else:
                    print(f"\n[{i}/{len(bloques)}] ⚙️  Ejecutando bloque SQL...")

                inicio_bloque = time.time()
                conn.execute(text(bloque_limpio))
                # No necesita commit explícito con begin()
                duracion_bloque = time.time() - inicio_bloque

                if duracion_bloque > 1:
                    print(f"     ✓ Completado en {duracion_bloque:.1f}s ({duracion_bloque/60:.1f} min)")

        duracion_total = time.time() - inicio_total

        print("\n" + "="*80)
        print("✅ KPIs LITE CREADOS EXITOSAMENTE")
        print("="*80)
        print(f"⏱️  Tiempo total: {duracion_total:.1f}s ({duracion_total/60:.1f} minutos)")

        print("\n📊 Vistas materializadas creadas:")
        print("   ✓ kpi_segmentacion_demografica_lite")
        print("   ✓ kpi_financiamiento_lite")
        print("   ✓ kpi_antiguedad_vehiculos_lite")
        print("   ✓ kpi_demanda_activa_lite")

        print("\n🔧 Función creada:")
        print("   ✓ refresh_kpis_lite()")

        print("\n💡 Próximos pasos:")
        print("   1. Verificar datos: python backend/scripts/actualizar_kpis.py --stats")
        print("   2. Actualizar cuando haya nuevos datos: SELECT refresh_kpis_lite();")
        print("   3. Usar en dashboard y ML")

        print("\n🚀 Opción futura: Si necesitas más dimensiones, ejecuta la versión completa:")
        print("   python backend/scripts/actualizar_kpis.py --inicializar")
        print("   (Tarda 30-60 minutos pero tiene todas las dimensiones)")
        print("="*80 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Error al crear KPIs LITE: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    crear_kpis_lite()
