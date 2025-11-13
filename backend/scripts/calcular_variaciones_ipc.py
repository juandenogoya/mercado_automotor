"""
Script para calcular variaciones de IPC a partir del nivel_general.

Como la API de INDEC no retorna las series de variación_mensual y variacion_interanual,
las calculamos nosotros a partir del nivel_general.

Fórmulas:
- Variación Mensual (%) = ((nivel_actual - nivel_anterior) / nivel_anterior) × 100
- Variación Interanual (%) = ((nivel_actual - nivel_hace_12_meses) / nivel_hace_12_meses) × 100
- Variación Acumulada (%) = ((nivel_actual - nivel_enero) / nivel_enero) × 100

Uso:
    python backend/scripts/calcular_variaciones_ipc.py
"""
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from loguru import logger
from backend.config.logger import setup_logger
from backend.utils.database import get_db
from backend.models.ipc import IPC


def calcular_variaciones_ipc():
    """
    Calcula las variaciones de IPC a partir del nivel_general.
    """
    logger.info("="*80)
    logger.info("CÁLCULO DE VARIACIONES IPC")
    logger.info("="*80)

    with get_db() as db:
        # 1. Obtener todos los registros ordenados por fecha
        logger.info("\n1. Cargando registros de IPC...")
        registros = db.query(IPC).order_by(IPC.fecha).all()

        if not registros:
            logger.error("No se encontraron registros de IPC")
            return 0

        logger.success(f"✓ {len(registros)} registros cargados")

        # 2. Calcular variaciones
        logger.info("\n2. Calculando variaciones...")

        updated_count = 0

        for i, registro in enumerate(registros):
            nivel_actual = float(registro.nivel_general)

            # Variación Mensual (comparar con mes anterior)
            if i > 0:
                nivel_anterior = float(registros[i-1].nivel_general)
                variacion_mensual = ((nivel_actual - nivel_anterior) / nivel_anterior) * 100
            else:
                variacion_mensual = None  # Primer registro no tiene anterior

            # Variación Interanual (comparar con hace 12 meses)
            if i >= 12:
                nivel_hace_12 = float(registros[i-12].nivel_general)
                variacion_interanual = ((nivel_actual - nivel_hace_12) / nivel_hace_12) * 100
            else:
                variacion_interanual = None  # Primeros 12 meses no tienen comparación

            # Variación Acumulada del año (comparar con enero del mismo año)
            if registro.mes == 1:
                # Enero: base del año
                variacion_acumulada = None
            else:
                # Buscar enero del mismo año
                enero_mismo_anio = next((r for r in registros if r.anio == registro.anio and r.mes == 1), None)
                if enero_mismo_anio:
                    nivel_enero = float(enero_mismo_anio.nivel_general)
                    variacion_acumulada = ((nivel_actual - nivel_enero) / nivel_enero) * 100
                else:
                    variacion_acumulada = None

            # Actualizar registro si cambió algo
            needs_update = False

            if variacion_mensual is not None:
                nuevo_val_mensual = Decimal(str(round(variacion_mensual, 2)))
                if registro.variacion_mensual is None or abs(float(registro.variacion_mensual) - float(nuevo_val_mensual)) > 0.01:
                    registro.variacion_mensual = nuevo_val_mensual
                    needs_update = True

            if variacion_interanual is not None:
                nuevo_val_interanual = Decimal(str(round(variacion_interanual, 2)))
                if registro.variacion_interanual is None or abs(float(registro.variacion_interanual) - float(nuevo_val_interanual)) > 0.01:
                    registro.variacion_interanual = nuevo_val_interanual
                    needs_update = True

            if variacion_acumulada is not None:
                nuevo_val_acumulada = Decimal(str(round(variacion_acumulada, 2)))
                if registro.variacion_acumulada is None or abs(float(registro.variacion_acumulada or 0) - float(nuevo_val_acumulada)) > 0.01:
                    registro.variacion_acumulada = nuevo_val_acumulada
                    needs_update = True

            if needs_update:
                registro.updated_at = datetime.utcnow()
                updated_count += 1

        # 3. Guardar cambios
        db.commit()

        logger.success(f"\n✓ {updated_count} registros actualizados")

        # 4. Mostrar ejemplos
        logger.info("\n3. Verificación - Últimos 5 meses:")
        logger.info("-" * 80)
        logger.info(f"{'Fecha':<12} {'Nivel':<12} {'Var.Mens.':<12} {'Var.Inter.':<12} {'Var.Acum.':<12}")
        logger.info("-" * 80)

        for registro in registros[-5:]:
            nivel = float(registro.nivel_general)
            var_mens = float(registro.variacion_mensual or 0)
            var_inter = float(registro.variacion_interanual or 0)
            var_acum = float(registro.variacion_acumulada or 0)

            logger.info(
                f"{str(registro.fecha):<12} {nivel:<12.2f} {var_mens:<12.2f}% {var_inter:<12.2f}% {var_acum:<12.2f}%"
            )

        return updated_count


def main():
    """Función principal."""
    setup_logger()

    logger.info("="*80)
    logger.info("🧮 CALCULAR VARIACIONES IPC DESDE NIVEL GENERAL")
    logger.info("="*80)
    logger.info("\nEste script calcula:")
    logger.info("  - Variación Mensual (% vs mes anterior)")
    logger.info("  - Variación Interanual (% vs mismo mes año anterior)")
    logger.info("  - Variación Acumulada (% vs enero del año)")
    logger.info("")

    updated_count = calcular_variaciones_ipc()

    logger.info("\n" + "="*80)
    logger.success("✅ PROCESO COMPLETADO")
    logger.info("="*80)
    logger.info(f"  Registros actualizados: {updated_count}")
    logger.info("\n📋 PRÓXIMOS PASOS:")
    logger.info("  1. Re-expandir IPC diario: python manage.py expandir-ipc-diario --export-excel ipc_diario.xlsx")
    logger.info("  2. Recalcular indicadores: python manage.py calcular-indicadores --limpiar --export-excel indicadores_macro.xlsx")
    logger.info("="*80)


if __name__ == "__main__":
    main()
