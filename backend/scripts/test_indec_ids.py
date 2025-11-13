"""
Script para probar y encontrar los IDs correctos de series IPC del INDEC.
"""
import requests
from datetime import date
from dateutil.relativedelta import relativedelta

# IDs a probar
IDS_TO_TEST = [
    # IDs actuales (que fallan)
    '148.3_INIVELNAL_DICI_M_26',
    '148.3_INIVELNALNAL_DICI_M_32',
    '148.3_INIVELNALNAL_DICI_M_31',

    # IDs alternativos encontrados en documentación
    '103.1_I2NG_2016_M_22',  # IPC Nivel General (base 2016)
    '103.1_I2N_2016_M_19',   # IPC variación mensual
    '103.1_I2N_2016_M_15',   # IPC variación interanual

    # Otros posibles
    '148.3_IPCNGNACIONA_0_M_26',
    '148.3_0_M_31',
]

def test_serie_id(serie_id):
    """Prueba si un ID de serie funciona."""
    fecha_hasta = date.today()
    fecha_desde = fecha_hasta - relativedelta(months=3)

    url = "https://apis.datos.gob.ar/series/api/series/"
    params = {
        'ids': serie_id,
        'limit': 5,
        'format': 'json',
        'start_date': fecha_desde.strftime('%Y-%m-%d'),
        'end_date': fecha_hasta.strftime('%Y-%m-%d')
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                print(f"✅ {serie_id:40s} - OK ({len(data['data'])} registros)")
                print(f"   Muestra: {data['data'][:2]}")
                return True
            else:
                print(f"⚠️  {serie_id:40s} - OK pero sin datos")
                return False
        else:
            print(f"❌ {serie_id:40s} - HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ {serie_id:40s} - Error: {str(e)[:50]}")
        return False

print("="*80)
print("PROBANDO IDs DE SERIES IPC DEL INDEC")
print("="*80)
print()

working_ids = []

for serie_id in IDS_TO_TEST:
    if test_serie_id(serie_id):
        working_ids.append(serie_id)
    print()

print("="*80)
print("RESUMEN")
print("="*80)
print(f"IDs funcionando: {len(working_ids)}")
for sid in working_ids:
    print(f"  - {sid}")
