"""
Códigos de SIOGRANOS para usar en consultas API
Fuente: TABLAS_SioGranos.xlsx
"""

# TABLA 1: PRODUCTOS
PRODUCTOS = {
    1: "TRIGO PAN",
    2: "MAIZ",
    3: "SORGO",
    11: "TRIGO CANDEAL",
    13: "CEBADA FORRAJERA",
    14: "CEBADA CERVECERA",
    20: "GIRASOL",
    21: "SOJA",  # ← PRINCIPAL para correlación con pick-ups
    45: "ACEITE DE SOJA",
    95: "ARROZ C. LARGO FINO",
    96: "ARROZ C. LARGO ANCHO",
}

# TABLA 2: PROVINCIAS
PROVINCIAS = {
    'A': "SALTA",
    'B': "BUENOS AIRES",  # ← Provincia con mayor actividad agrícola
    'C': "CAPITAL FEDERAL",
    'D': "SAN LUIS",
    'E': "ENTRE RIOS",  # ← Alta actividad agrícola
    'F': "LA RIOJA",
    'G': "SANTIAGO DEL ESTERO",
    'H': "CHACO",
    'J': "SAN JUAN",
    'K': "CATAMARCA",
    'L': "LA PAMPA",  # ← Alta actividad agrícola
    'M': "MENDOZA",
    'N': "MISIONES",
    'P': "FORMOSA",
    'Q': "NEUQUEN",
    'R': "RIO NEGRO",
    'S': "SANTA FE",  # ← Alta actividad agrícola
    'T': "TUCUMAN",
    'U': "CHUBUT",
    'V': "TIERRA DEL FUEGO",
    'W': "CORRIENTES",
    'X': "CORDOBA",  # ← Alta actividad agrícola
    'Y': "JUJUY",
    'Z': "SANTA CRUZ",
}

# Provincias clave para análisis automotor (zona pampeana)
PROVINCIAS_AGRICOLAS_PRINCIPALES = ['B', 'S', 'X', 'E', 'L']

# TABLA 3: MONEDAS
MONEDAS = {
    1: "PESOS",
    2: "DOLARES",
    6: "EUROS",
}

# TABLA 4: TIPOS DE CONTRATOS
TIPOS_CONTRATOS = {
    1: "CONTRATO A PRECIO HECHO",
    3: "CONTRATO A FIJAR PRECIO",
}

# TABLA 6: MODALIDAD OPERACION
MODALIDAD_OPERACION = {
    1: "Compraventa",
    2: "Operación de Canje",
}

# TABLA 7: TIPO ESTADO
TIPO_ESTADO = {
    1: "Borrador",
    2: "Informada",
    3: "Observada",
    4: "Objetada",
}

# TABLA 8: CONDICION PAGO
CONDICION_PAGO = {
    1: "Contra entrega",
    2: "Anticipado a la entrega",
    3: "A plazo",
}

# TABLA 9: TIPO OPERACIÓN
TIPO_OPERACION = {
    1: "Contrato",
    4: "Anulación",
    5: "Rectificación",
    6: "Fijación",
    7: "Rectificación Fijación",
    8: "Anulación Fijación",
    9: "Rectificación Ampliación",
    10: "Anulación Ampliación",
    11: "Ampliación",
}

# TABLA 10: TIPO CONDICION CALIDAD
TIPO_CONDICION_CALIDAD = {
    1: "Condiciones Cámara",
    4: "Condiciones Fábrica",
    5: "Art. 12",
    6: "Otra",
    7: "Crudo Desgomado",
    8: "Neutralizado",
}

# TABLA 11: ZONAS
ZONAS = {
    1: "Zona 1", 2: "Zona 2", 3: "Zona 3", 4: "Zona 4", 5: "Zona 5",
    6: "Zona 6", 7: "Zona 7", 8: "Zona 8", 9: "Zona 9", 10: "Zona 10",
    11: "Zona 11", 12: "Zona 12", 13: "Zona 13", 14: "Zona 14", 15: "Zona 15",
    16: "Zona 16", 17: "Zona 17", 18: "Zona 18",
    19: "Quequén",
    20: "B. Blanca",
    21: "Cordoba",
    22: "Bs As",
    23: "Rosario N",
    24: "Rosario S",
    25: "Zona 25",
    26: "Zona 26",
}

# Productos relevantes para análisis automotor (ordenados por importancia)
PRODUCTOS_CLAVE = [
    21,  # SOJA - Principal exportación y motor económico rural
    2,   # MAIZ - Segundo en importancia
    1,   # TRIGO PAN
    20,  # GIRASOL
]
