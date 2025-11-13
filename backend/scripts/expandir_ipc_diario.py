"""
Script para expandir IPC mensual a frecuencia diaria.

Lógica (Opción B - Vigencia):
- IPC Septiembre 2024 = 2.5%
- Se aplica TODO octubre 2024 (1-31 octubre)
- Cada día de octubre tiene el valor 2.5%

Uso:
    python backend/scripts/expandir_ipc_diario.py
    python backend/scripts/expandir_ipc_diario.py --export-excel ipc_diario.xlsx
"""
import sys
import argparse
from pathlib import Path
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from loguru import logger
from backend.config.logger import setup_logger
from backend.utils.database import get_db, init_db
from backend.models.ipc import IPC
from backend.models.ipc_diario import IPCDiario


def obtener_dias_del_mes(fecha: date) -> int:
    """
    Obtiene el número de días de un mes específico.

    Args:
        fecha: Fecha dentro del mes

    Returns:
        Número de días del mes (28-31)
    """
    # Obtener el primer día del mes siguiente
    if fecha.month == 12:
        siguiente_mes = date(fecha.year + 1, 1, 1)
    else:
        siguiente_mes = date(fecha.year, fecha.month + 1, 1)

    # Restar un día para obtener el último día del mes actual
    ultimo_dia = siguiente_mes - timedelta(days=1)

    return ultimo_dia.day


def expandir_ipc_mensual_a_diario() -> tuple[int, pd.DataFrame]:
    """
    Expande IPC mensual a frecuencia diaria usando período de vigencia.

    Lógica:
    - IPC del mes M se aplica a TODO el mes M+1
    - Ejemplo: IPC Sept (mes 9) → se aplica a Oct (mes 10)

    Returns:
        Tuple con (registros_guardados, DataFrame para Excel)
    """
    logger.info("="*80)
    logger.info("EXPANSIÓN DE IPC MENSUAL A DIARIO (Opción B - Vigencia)")
    logger.info("="*80)

    # 1. Leer datos mensuales
    logger.info("\n1. Leyendo IPC mensual desde base de datos...")

    # Leer y convertir a diccionarios dentro del contexto de DB
    ipc_data = []
    with get_db() as db:
        ipc_query = db.query(IPC).order_by(IPC.fecha).all()

        # Convertir a diccionarios para evitar problemas con sesiones cerradas
        for registro in ipc_query:
            ipc_data.append({
                'fecha': registro.fecha,
                'variacion_mensual': registro.variacion_mensual,
                'nivel_general': registro.nivel_general
            })

    if not ipc_data:
        logger.error("No se encontraron registros de IPC mensual en la base de datos")
        return 0, pd.DataFrame()

    logger.success(f"✓ Obtenidos {len(ipc_data)} registros mensuales")

    # 2. Expandir a diario
    logger.info("\n2. Expandiendo a frecuencia diaria...")

    registros_diarios = []
    datos_para_excel = []

    for registro in ipc_data:
        # Período medido (el mes que midió) - asegurar que sea objeto date
        periodo_medido = registro['fecha']
        if not isinstance(periodo_medido, date):
            # Si es datetime, convertir a date
            periodo_medido = periodo_medido.date()

        # Período de vigencia (mes siguiente)
        periodo_vigencia = periodo_medido + relativedelta(months=1)

        # Obtener número de días del mes de vigencia
        dias_en_mes = obtener_dias_del_mes(periodo_vigencia)

        # Obtener variación mensual (puede ser None)
        var_mensual = float(registro['variacion_mensual'] or 0)

        logger.info(
            f"  IPC {periodo_medido.strftime('%Y-%m')} = {var_mensual}% "
            f"→ Aplicar a {periodo_vigencia.strftime('%Y-%m')} ({dias_en_mes} días)"
        )

        # Generar un registro por cada día del mes de vigencia
        for dia in range(1, dias_en_mes + 1):
            fecha_dia = date(periodo_vigencia.year, periodo_vigencia.month, dia)

            # Calcular días desde publicación (asumiendo publicación ~15 del mes)
            fecha_publicacion_estimada = periodo_vigencia.replace(day=15)
            if fecha_dia >= fecha_publicacion_estimada:
                dias_desde_pub = (fecha_dia - fecha_publicacion_estimada).days
            else:
                dias_desde_pub = None

            registro_diario = {
                'fecha': fecha_dia,
                'ipc_mensual': var_mensual,
                'periodo_medido': periodo_medido,
                'periodo_vigencia': periodo_vigencia,
                'dias_desde_publicacion': dias_desde_pub,
                'anio': fecha_dia.year,
                'mes': fecha_dia.month,
                'fuente': 'INDEC_DIARIO'
            }

            registros_diarios.append(registro_diario)

            # Para Excel (más legible)
            datos_para_excel.append({
                'Fecha': fecha_dia.strftime('%Y-%m-%d'),
                'IPC Mensual (%)': var_mensual,
                'Período Medido': periodo_medido.strftime('%Y-%m'),
                'Período Vigencia': periodo_vigencia.strftime('%Y-%m'),
                'Año': fecha_dia.year,
                'Mes': fecha_dia.month,
                'Día': fecha_dia.day,
                'Días desde Publicación': dias_desde_pub
            })

    logger.success(f"✓ Generados {len(registros_diarios)} registros diarios")

    # 3. Guardar en base de datos
    logger.info("\n3. Guardando en PostgreSQL (tabla ipc_diario)...")

    saved_count = 0
    with get_db() as db:
        for registro in registros_diarios:
            try:
                # Verificar si existe
                existing = db.query(IPCDiario).filter(
                    IPCDiario.fecha == registro['fecha']
                ).first()

                if not existing:
                    ipc_diario = IPCDiario(**registro)
                    db.add(ipc_diario)
                    saved_count += 1
                else:
                    # Actualizar si cambió
                    if float(existing.ipc_mensual) != registro['ipc_mensual']:
                        existing.ipc_mensual = registro['ipc_mensual']
                        existing.periodo_medido = registro['periodo_medido']
                        existing.periodo_vigencia = registro['periodo_vigencia']

            except Exception as e:
                logger.warning(f"Error guardando registro {registro['fecha']}: {e}")
                continue

        db.commit()

    logger.success(f"✓ Guardados {saved_count} nuevos registros en PostgreSQL")

    # 4. Crear DataFrame para Excel
    df = pd.DataFrame(datos_para_excel)

    logger.info("\n" + "="*80)
    logger.success(f"✅ EXPANSIÓN COMPLETADA")
    logger.info("="*80)
    logger.info(f"  Registros mensuales: {len(ipc_data)}")
    logger.info(f"  Registros diarios generados: {len(registros_diarios)}")
    logger.info(f"  Registros guardados en BD: {saved_count}")
    logger.info(f"  Período: {registros_diarios[0]['fecha']} a {registros_diarios[-1]['fecha']}")
    logger.info("="*80)

    return saved_count, df


def exportar_a_excel(df: pd.DataFrame, filename: str):
    """
    Exporta DataFrame a Excel con formato.

    Args:
        df: DataFrame con los datos
        filename: Nombre del archivo Excel
    """
    logger.info(f"\n📊 Exportando a Excel: {filename}")

    try:
        # Crear writer con formato
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Hoja 1: Datos completos
            df.to_excel(writer, sheet_name='IPC Diario', index=False)

            # Hoja 2: Resumen por mes
            resumen = df.groupby(['Período Vigencia']).agg({
                'IPC Mensual (%)': 'first',
                'Fecha': 'count'
            }).rename(columns={'Fecha': 'Días'}).reset_index()

            resumen.to_excel(writer, sheet_name='Resumen Mensual', index=False)

            # Hoja 3: Primeros y últimos 30 días (para verificación)
            df_head = df.head(30)
            df_tail = df.tail(30)

            df_head.to_excel(writer, sheet_name='Primeros 30 días', index=False)
            df_tail.to_excel(writer, sheet_name='Últimos 30 días', index=False)

        logger.success(f"✅ Excel creado exitosamente: {filename}")
        logger.info(f"  Hojas: IPC Diario, Resumen Mensual, Primeros 30 días, Últimos 30 días")
        logger.info(f"  Total registros: {len(df):,}")

    except Exception as e:
        logger.error(f"❌ Error creando Excel: {e}")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Expandir IPC mensual a frecuencia diaria",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--export-excel',
        type=str,
        help='Nombre del archivo Excel a exportar (ej: ipc_diario.xlsx)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logger()

    # Inicializar BD (crear tabla si no existe)
    logger.info("Inicializando base de datos...")
    init_db()
    logger.success("✓ Base de datos inicializada\n")

    # Expandir IPC
    saved_count, df = expandir_ipc_mensual_a_diario()

    if saved_count > 0:
        logger.success(f"\n🎉 Proceso completado: {saved_count} registros diarios en PostgreSQL")

        # Exportar a Excel si se especificó
        if args.export_excel:
            exportar_a_excel(df, args.export_excel)
        else:
            logger.info("\n💡 Para exportar a Excel: python backend/scripts/expandir_ipc_diario.py --export-excel ipc_diario.xlsx")

    else:
        logger.warning("\n⚠️  No se guardaron nuevos registros (posiblemente ya existen)")


if __name__ == "__main__":
    main()
