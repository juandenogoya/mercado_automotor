"""
Script mejorado para identificar qué representa cada serie IPC.
Trae más datos para poder identificar si son índices, variaciones, etc.
"""
import requests
from datetime import date
from dateutil.relativedelta import relativedelta
import json

# IDs que funcionaron
WORKING_IDS = {
    '148.3_INIVELNAL_DICI_M_26': 'Nivel General (actual)',
    '103.1_I2N_2016_M_19': 'Desconocido 1',
    '103.1_I2N_2016_M_15': 'Desconocido 2',
}

def get_serie_metadata(serie_id):
    """Obtiene metadata de una serie."""
    url = "https://apis.datos.gob.ar/series/api/series/"
    params = {
        'ids': serie_id,
        'metadata': 'full'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_serie_data(serie_id, months=12):
    """Obtiene datos históricos de una serie."""
    fecha_hasta = date.today()
    fecha_desde = fecha_hasta - relativedelta(months=months)

    url = "https://apis.datos.gob.ar/series/api/series/"
    params = {
        'ids': serie_id,
        'limit': 100,
        'format': 'json',
        'start_date': fecha_desde.strftime('%Y-%m-%d'),
        'end_date': fecha_hasta.strftime('%Y-%m-%d')
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

print("="*80)
print("ANÁLISIS DETALLADO DE SERIES IPC FUNCIONALES")
print("="*80)
print()

for serie_id, descripcion in WORKING_IDS.items():
    print("="*80)
    print(f"SERIE: {serie_id}")
    print(f"Descripción actual: {descripcion}")
    print("="*80)

    # Obtener metadata
    print("\n1. METADATA:")
    metadata = get_serie_metadata(serie_id)
    if metadata:
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
    else:
        print("   No se pudo obtener metadata")

    # Obtener datos históricos
    print("\n2. ÚLTIMOS 12 MESES DE DATOS:")
    data = get_serie_data(serie_id, months=12)
    if data and 'data' in data:
        valores = data['data']
        print(f"   Total registros: {len(valores)}")
        print(f"\n   Últimos 6 valores:")
        for i, valor in enumerate(valores[-6:]):
            print(f"   {valor[0]:12s}: {valor[1]:10.2f}")

        # Calcular variaciones para identificar qué tipo de serie es
        if len(valores) >= 2:
            print(f"\n3. ANÁLISIS DE VARIACIONES:")
            ultimo = valores[-1][1]
            penultimo = valores[-2][1]
            var_absoluta = ultimo - penultimo
            var_porcentual = (var_absoluta / penultimo) * 100

            print(f"   Último valor: {ultimo:.2f}")
            print(f"   Penúltimo valor: {penultimo:.2f}")
            print(f"   Variación absoluta: {var_absoluta:.2f}")
            print(f"   Variación %: {var_porcentual:.2f}%")

            # Identificar tipo de serie según valores
            if ultimo > 100 and ultimo < 20000:
                print(f"\n   >>> INTERPRETACIÓN: Parece un ÍNDICE BASE")
            elif ultimo < 20 and ultimo > 0:
                print(f"\n   >>> INTERPRETACIÓN: Parece una VARIACIÓN PORCENTUAL")
            else:
                print(f"\n   >>> INTERPRETACIÓN: Tipo desconocido")
    else:
        print("   No se pudieron obtener datos")

    print("\n" + "="*80)
    print()

print("="*80)
print("RECOMENDACIÓN FINAL")
print("="*80)
print("""
Basado en el análisis anterior:
- Si todos tienen valores >100, son diferentes índices base (no variaciones)
- Necesitaremos calcular las variaciones nosotros mismos
- O buscar otras series que tengan las variaciones pre-calculadas
""")
