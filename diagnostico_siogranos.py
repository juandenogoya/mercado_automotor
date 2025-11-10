"""
Script de diagnóstico para API SIOGRANOS
Prueba diferentes rangos de fechas para entender el comportamiento
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv(
    'SIOGRANOS_API_URL',
    'https://test.bc.org.ar/SiogranosAPI/api/ConsultaPublica/consultarOperaciones'
)

def probar_rango(fecha_desde: str, fecha_hasta: str):
    """Prueba un rango de fechas específico"""
    print(f"\n{'='*60}")
    print(f"Probando: {fecha_desde} → {fecha_hasta}")
    print(f"{'='*60}")

    params = {
        'FechaOperacionDesde': fecha_desde,
        'FechaOperacionHasta': fecha_hasta
    }

    try:
        response = requests.get(API_URL, params=params, timeout=30)

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Estructura: {type(data)}")

            if isinstance(data, dict):
                print(f"Claves: {list(data.keys())}")
                print(f"Success: {data.get('success')}")
                print(f"Message: {data.get('message')}")

                if 'result' in data:
                    result = data['result']
                    print(f"Result type: {type(result)}")

                    if isinstance(result, dict) and 'operaciones' in result:
                        ops = result['operaciones']
                        print(f"Operaciones type: {type(ops)}")

                        if ops is None:
                            print(f"⚠️  Operaciones: NULL")
                        elif isinstance(ops, list):
                            print(f"✓ Operaciones: {len(ops)} registros")
                            if len(ops) > 0:
                                print(f"  Primera operación: {list(ops[0].keys())[:5]}")
                        else:
                            print(f"? Operaciones: {ops}")
        else:
            print(f"❌ Error: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Excepción: {e}")


if __name__ == "__main__":
    print(f"\n{'#'*60}")
    print("DIAGNÓSTICO API SIOGRANOS")
    print(f"{'#'*60}")
    print(f"API: {API_URL}")

    # Probar diferentes rangos

    # 1. Rango muy reciente (últimos 7 días)
    hoy = datetime.now()
    hace_7_dias = hoy - timedelta(days=7)
    probar_rango(hace_7_dias.strftime('%Y-%m-%d'), hoy.strftime('%Y-%m-%d'))

    # 2. Rango reciente pero completo (hace 1 mes)
    hace_1_mes = hoy - timedelta(days=30)
    hace_23_dias = hoy - timedelta(days=23)
    probar_rango(hace_1_mes.strftime('%Y-%m-%d'), hace_23_dias.strftime('%Y-%m-%d'))

    # 3. Rango que sabemos que funcionó (2020-01-29 a 2020-02-05)
    probar_rango('2020-01-29', '2020-02-05')

    # 4. Rango que sabemos que funcionó (2020-02-05 a 2020-02-12)
    probar_rango('2020-02-05', '2020-02-12')

    # 5. Rango que falló (2020-02-12 a 2020-02-19)
    probar_rango('2020-02-12', '2020-02-19')

    # 6. Rango en marzo 2020 (que devuelve null)
    probar_rango('2020-03-04', '2020-03-11')

    # 7. Probar un solo día reciente
    ayer = hoy - timedelta(days=1)
    probar_rango(ayer.strftime('%Y-%m-%d'), ayer.strftime('%Y-%m-%d'))

    # 8. Probar un chunk más pequeño en febrero
    probar_rango('2020-02-12', '2020-02-15')

    print(f"\n{'#'*60}")
    print("FIN DIAGNÓSTICO")
    print(f"{'#'*60}\n")
