"""
Test rápido para validar series del INDEC.
Script standalone sin dependencias del backend.
"""
import requests
from datetime import date

# IDs de series a validar
SERIES_IDS = {
    # IPC
    'ipc_nacional': '148.3_INIVELNAL_DICI_M_26',
    'ipc_alimentos': '148.3_INALIBED_DICI_M_29',
    'ipc_transporte': '148.3_INTRANSP_DICI_M_33',
    'ipc_core': '148.3_INUCLEOD_DICI_M_40',

    # Salarios
    'salario_indice': '11.3_ISAC_0_M_18',
    'salario_privado': '11.3_ISAPRI_0_M_22',
    'salario_publico': '11.3_ISAPUB_0_M_24',

    # Actividad Económica
    'emae': '143.3_NO_PR_2004_A_21',
    'emae_desest': '143.3_NO_PR_2004_A_28',

    # Producción Industrial
    'ipi_general': '133.2_OFIEIBOV_DICI_M_19',
    'ipi_automotriz': '133.2_OFABAUT_DICI_M_42',

    # Comercio
    'ventas_super': '134.3_IVSMSTO_DICI_M_13',
    'ventas_shoppings': '134.4_IVSHSTO_DICI_M_17',

    # Construcción
    'isac': '137.2_ISBISTOD_DICI_M_16',

    # Empleo
    'empleo_privado': '11.5_ITCRP_0_M_21',
}

API_BASE = "https://apis.datos.gob.ar/series/api"

def test_series(series_id, nombre):
    """Test una serie individual."""
    url = f"{API_BASE}/series/"

    params = {
        'ids': series_id,
        'limit': 5  # Solo 5 puntos para testing
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        series_data = data.get('data', [])

        if series_data:
            print(f"✓ {nombre:25} | ID: {series_id} | {len(series_data)} puntos | Último: {series_data[-1]}")
            return True
        else:
            print(f"⚠ {nombre:25} | ID: {series_id} | Sin datos")
            return False

    except Exception as e:
        print(f"✗ {nombre:25} | ID: {series_id} | Error: {str(e)[:50]}")
        return False

def main():
    print("="*100)
    print("  VALIDACIÓN DE SERIES INDEC")
    print("="*100)
    print()

    results = {}

    for nombre, series_id in SERIES_IDS.items():
        result = test_series(series_id, nombre)
        results[nombre] = result

    print()
    print("="*100)
    print("  RESUMEN")
    print("="*100)

    valid_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"\nSeries válidas: {valid_count}/{total_count}")

    if valid_count < total_count:
        print("\nSeries con problemas:")
        for nombre, valid in results.items():
            if not valid:
                print(f"  - {nombre}: {SERIES_IDS[nombre]}")

    print()

if __name__ == "__main__":
    main()
