"""
Script de análisis para determinar longitudes máximas de campos SIOGRANOS
"""
import requests
from collections import defaultdict

API_URL = 'https://test.bc.org.ar/SiogranosAPI/api/ConsultaPublica/consultarOperaciones'

# Obtener muestra de datos
print("Consultando API SIOGRANOS...")
response = requests.get(API_URL, params={
    'FechaOperacionDesde': '2020-01-01',
    'FechaOperacionHasta': '2020-01-08'
}, timeout=30)

if response.status_code == 200:
    json_response = response.json()

    if isinstance(json_response, dict):
        if 'result' in json_response and 'operaciones' in json_response['result']:
            operaciones = json_response['result']['operaciones']
        elif 'operaciones' in json_response:
            operaciones = json_response['operaciones']
        else:
            operaciones = []
    elif isinstance(json_response, list):
        operaciones = json_response
    else:
        operaciones = []

    print(f"Total operaciones: {len(operaciones)}\n")

    # Analizar longitudes
    max_lengths = defaultdict(int)
    ejemplos = {}

    for op in operaciones:
        for key, value in op.items():
            if value is not None:
                str_val = str(value)
                if len(str_val) > max_lengths[key]:
                    max_lengths[key] = len(str_val)
                    ejemplos[key] = str_val

    # Mostrar resultados ordenados
    print("=" * 80)
    print("LONGITUDES MÁXIMAS POR CAMPO")
    print("=" * 80)

    for key in sorted(max_lengths.keys()):
        length = max_lengths[key]
        ejemplo = ejemplos[key]

        # Mostrar solo campos que podrían ser problemáticos
        if length > 10:
            print(f"{key:40} | Max: {length:4} chars | Ej: {ejemplo[:60]}")

    print("\n" + "=" * 80)
    print("CAMPOS STRING CRÍTICOS")
    print("=" * 80)

    # Enfocarnos en campos que almacenamos como VARCHAR
    campos_varchar = [
        'idOperacion', 'numeroOperacion',
        'idGrano', 'codigoGrano', 'nombreGrano', 'grano',
        'idMoneda', 'simboloMoneda', 'simboloPrecioPorTN', 'nombreMoneda', 'moneda',
        'idProvinciaProcedencia', 'procedenciaProvincia', 'nombreProvinciaProcedencia', 'provinciaProcedencia',
        'idLocalidadProcedencia', 'nombreLocalidadProcedencia', 'localidadProcedencia',
        'idProvinciaDestino', 'nombreProvinciaDestino', 'provinciaDestino',
        'idLocalidadDestino', 'nombreLocalidadDestino', 'localidadDestino',
        'idTipoOperacion', 'nombreTipoOperacion', 'tipoOperacion',
        'idTipoContrato', 'nombreTipoContrato', 'tipoContrato',
        'idModalidad', 'nombreModalidad', 'modalidad',
        'idEstado', 'nombreEstado', 'estado',
        'idCondicionPago', 'nombreCondicionPago', 'condicionPago',
        'idCondicionCalidad', 'nombreCondicionCalidad', 'condicionCalidad',
        'idZona', 'nombreZona', 'zona',
        'idPuerto', 'nombrePuerto', 'puerto'
    ]

    for campo in campos_varchar:
        if campo in max_lengths:
            length = max_lengths[campo]
            ejemplo = ejemplos[campo]
            print(f"{campo:40} | {length:4} chars | {ejemplo[:50]}")

else:
    print(f"Error: {response.status_code}")
