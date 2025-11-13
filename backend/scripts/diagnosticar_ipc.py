"""
Script de diagnóstico para verificar datos de IPC en PostgreSQL.
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.utils.database import get_db
from backend.models.ipc import IPC
from backend.models.ipc_diario import IPCDiario

print("="*80)
print("DIAGNÓSTICO DE DATOS IPC")
print("="*80)

with get_db() as db:
    # 1. Verificar IPC mensual (fuente original)
    print("\n1. IPC MENSUAL (datos originales de INDEC):")
    print("-" * 80)

    ipc_mensual = db.query(IPC).order_by(IPC.fecha).limit(10).all()

    if ipc_mensual:
        print(f"\n   Primeros 10 registros:")
        print(f"   {'Fecha':<12} {'Nivel General':<15} {'Var. Mensual':<15} {'Var. Interanual':<15}")
        print("   " + "-"*60)
        for r in ipc_mensual:
            print(f"   {str(r.fecha):<12} {float(r.nivel_general):<15.2f} {float(r.variacion_mensual or 0):<15.2f} {float(r.variacion_interanual or 0):<15.2f}")
    else:
        print("   ⚠️  NO HAY DATOS")

    # Contar cuántos tienen variacion_mensual != 0
    count_total = db.query(IPC).count()
    count_con_variacion = db.query(IPC).filter(IPC.variacion_mensual != None, IPC.variacion_mensual != 0).count()
    print(f"\n   Total registros: {count_total}")
    print(f"   Registros con variación mensual != 0: {count_con_variacion}")

    if count_con_variacion == 0:
        print("\n   ❌ PROBLEMA: Todos los registros de IPC mensual tienen variación_mensual en 0 o NULL")
        print("   ⚠️  ACCIÓN: Necesitas revisar la carga desde INDEC API")

    # 2. Verificar IPC diario (expandido)
    print("\n\n2. IPC DIARIO (expandido con Opción B):")
    print("-" * 80)

    ipc_diario = db.query(IPCDiario).order_by(IPCDiario.fecha).limit(10).all()

    if ipc_diario:
        print(f"\n   Primeros 10 registros:")
        print(f"   {'Fecha':<12} {'IPC Mensual':<15} {'Periodo Medido':<15} {'Periodo Vigencia':<15}")
        print("   " + "-"*60)
        for r in ipc_diario:
            print(f"   {str(r.fecha):<12} {float(r.ipc_mensual):<15.2f} {str(r.periodo_medido):<15} {str(r.periodo_vigencia):<15}")
    else:
        print("   ⚠️  NO HAY DATOS")

    # Contar cuántos tienen ipc_mensual != 0
    count_total_diario = db.query(IPCDiario).count()
    count_con_ipc = db.query(IPCDiario).filter(IPCDiario.ipc_mensual != 0).count()
    print(f"\n   Total registros: {count_total_diario}")
    print(f"   Registros con IPC mensual != 0: {count_con_ipc}")

    if count_con_ipc == 0:
        print("\n   ❌ PROBLEMA: Todos los registros de IPC diario tienen ipc_mensual en 0")
        print("   ⚠️  CAUSA: El problema viene del IPC mensual original")

    # 3. Ver un ejemplo específico del medio de la serie
    print("\n\n3. EJEMPLO ESPECÍFICO (registros del medio de la serie):")
    print("-" * 80)

    # IPC mensual de julio 2024 (debería tener ~3-4% de inflación)
    ejemplo_mensual = db.query(IPC).filter(
        IPC.fecha >= '2024-07-01',
        IPC.fecha < '2024-08-01'
    ).first()

    if ejemplo_mensual:
        print(f"\n   IPC Mensual - Julio 2024:")
        print(f"   Fecha: {ejemplo_mensual.fecha}")
        print(f"   Nivel General: {float(ejemplo_mensual.nivel_general)}")
        print(f"   Variación Mensual: {float(ejemplo_mensual.variacion_mensual or 0)}%")
        print(f"   Variación Interanual: {float(ejemplo_mensual.variacion_interanual or 0)}%")

        # Buscar IPC diario correspondiente (agosto 2024)
        ejemplo_diario = db.query(IPCDiario).filter(
            IPCDiario.fecha >= '2024-08-01',
            IPCDiario.fecha < '2024-08-05'
        ).first()

        if ejemplo_diario:
            print(f"\n   IPC Diario - Primeros días de Agosto 2024 (aplicando IPC de Julio):")
            print(f"   Fecha: {ejemplo_diario.fecha}")
            print(f"   IPC Mensual: {float(ejemplo_diario.ipc_mensual)}%")
            print(f"   Periodo Medido: {ejemplo_diario.periodo_medido} (debería ser 2024-07-01)")
            print(f"   Periodo Vigencia: {ejemplo_diario.periodo_vigencia} (debería ser 2024-08-01)")

print("\n" + "="*80)
print("DIAGNÓSTICO COMPLETADO")
print("="*80)
print("\nSi todos los valores están en 0, el problema está en la carga inicial desde INDEC.")
print("Verifica que la API de INDEC esté retornando datos correctos.")
