"""
Script para cargar datos históricos de BCRA e INDEC.
"""
from backend.api_clients import BCRAClient, INDECClient
from datetime import date

print('=== Cargando datos históricos ===')
print('Fecha tope: 05/11/2024\n')

# INDEC - últimos 6 meses
print('1. Cargando INDEC...')
indec = INDECClient()
result_indec = indec.sync_all_indicators(fecha_desde=date(2024, 5, 1))
ipc_saved = result_indec['indicadores']['ipc'].get('records_saved', 0)
print(f'   IPC: {ipc_saved} registros')

# BCRA - últimos 3 meses
print('\n2. Cargando BCRA...')
bcra = BCRAClient()
result_bcra = bcra.sync_all_indicators(fecha_desde=date(2024, 8, 1), fecha_hasta=date(2024, 11, 5))
print(f'   BCRA: {result_bcra["records_saved"]} registros')

print('\n✅ Carga completada')
print(f'\nTotal registros cargados: {ipc_saved + result_bcra["records_saved"]}')
