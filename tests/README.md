# Tests - Mercado Automotor

Suite completa de tests para el Sistema de Inteligencia Comercial del Mercado Automotor.

## 📊 Cobertura de Tests

La suite de tests cubre los siguientes componentes:

### ✅ Tests Unitarios (Rápidos)
- **test_validators.py**: Validadores Pydantic para datos scrapeados (80+ tests)
- **test_indicadores.py**: Cálculo de indicadores estratégicos (40+ tests)
- **test_models.py**: Modelos de base de datos y queries (30+ tests)
- **test_api_clients.py**: API clients con mocking (20+ tests)

### 🔄 Tests de Integración (Lentos)
- **test_scrapers_real.py**: Scrapers con datos reales de sitios web

**Total**: ~200+ tests

## 🚀 Ejecución Rápida

```bash
# Todos los tests
./run_tests.sh

# Solo tests unitarios (rápidos)
./run_tests.sh unit

# Con reporte de cobertura
./run_tests.sh coverage

# Tests específicos
./run_tests.sh validators
./run_tests.sh indicadores
./run_tests.sh models
```

## 📖 Guía de Tests

### 1. Tests de Validadores

**Archivo**: `test_validators.py`

**Cobertura**:
- Validación de datos de patentamientos (ACARA/FACCARA)
- Validación de datos de producción (ADEFA)
- Validación de indicadores BCRA
- Validación de listados de MercadoLibre
- Función `validate_data()` con datasets mixtos

**Ejemplo**:
```bash
pytest tests/test_validators.py -v
```

**Tests Clave**:
- ✅ Datos válidos pasan validación
- ✅ Datos inválidos son rechazados con mensajes claros
- ✅ Normalización de campos (marcas, terminales)
- ✅ Validación de rangos (precios, fechas, tasas)

### 2. Tests de Indicadores

**Archivo**: `test_indicadores.py`

**Cobertura**:
- Índice de Tensión de Demanda
- Rotación de Stock por Terminal
- Índice de Accesibilidad de Compra
- Ranking de Atención de Marca
- Función `guardar_indicadores()`

**Ejemplo**:
```bash
pytest tests/test_indicadores.py -v
```

**Tests Clave**:
- ✅ Cálculo con datos completos
- ✅ Manejo de datos faltantes
- ✅ Estructura correcta de indicadores
- ✅ Guardado en base de datos
- ✅ Actualización de duplicados

### 3. Tests de Modelos

**Archivo**: `test_models.py`

**Cobertura**:
- Modelo Patentamiento
- Modelo Produccion
- Modelo BCRAIndicador
- Modelo MercadoLibreListing
- Modelo IndicadorCalculado
- Relaciones entre modelos

**Ejemplo**:
```bash
pytest tests/test_models.py -v
```

**Tests Clave**:
- ✅ Creación de registros
- ✅ Queries y filtros
- ✅ Timestamps automáticos
- ✅ Constraints únicos
- ✅ Campos JSON

### 4. Tests de API Clients

**Archivo**: `test_api_clients.py`

**Cobertura**:
- BCRAClient (con mocking)
- MercadoLibreClient (con mocking)
- Rate limiting
- Manejo de errores
- Paginación

**Ejemplo**:
```bash
pytest tests/test_api_clients.py -v
```

**Tests Clave**:
- ✅ Requests exitosos
- ✅ Manejo de errores HTTP
- ✅ Respeto de rate limits
- ✅ Parsing de respuestas JSON
- ✅ Paginación automática

### 5. Tests de Scrapers (Integración)

**Archivo**: `test_scrapers_real.py`

⚠️ **IMPORTANTE**: Estos tests hacen requests REALES a sitios web. Úsalos con moderación.

**Cobertura**:
- Conexión a ACARA/FACCARA
- Conexión a ADEFA
- Análisis de estructura HTML
- Parsing de períodos
- Extracción de reportes

**Ejemplo**:
```bash
# Solo tests de integración
./run_tests.sh integration

# O específicamente scrapers
pytest tests/test_scrapers_real.py -v -m integration
```

## 🎯 Markers de Pytest

Los tests usan markers para categorización:

```python
@pytest.mark.unit          # Tests unitarios rápidos
@pytest.mark.slow          # Tests lentos (scrapers)
@pytest.mark.integration   # Tests de integración (requieren servicios externos)
@pytest.mark.requires_db   # Tests que requieren base de datos
```

**Uso**:
```bash
# Solo tests unitarios
pytest -m "not slow" -v

# Solo tests de integración
pytest -m integration -v

# Excluir tests lentos
pytest -m "not slow and not integration" -v
```

## 📈 Reporte de Cobertura

Generar reporte completo:

```bash
./run_tests.sh coverage
```

Esto genera:
- Reporte en terminal con líneas no cubiertas
- Reporte HTML en `htmlcov/index.html`

**Objetivo**: > 60% de cobertura

Ver reporte HTML:
```bash
# Linux/Mac
open htmlcov/index.html

# Windows
start htmlcov/index.html
```

## 🛠️ Fixtures Compartidos

**Archivo**: `conftest.py`

Fixtures disponibles para todos los tests:

```python
# Database
db_session              # Sesión de BD en memoria
test_engine             # Engine de BD para tests

# Fechas
sample_fecha            # Fecha de ejemplo: 2024-01-15
sample_fecha_rango      # Rango de fechas (30 días)

# Datos de ejemplo
sample_patentamiento_data
sample_produccion_data
sample_bcra_data
sample_meli_data
```

## 🔧 Configuración

**Archivo**: `pytest.ini`

```ini
[pytest]
markers =
    slow: Tests lentos
    integration: Tests de integración
    unit: Tests unitarios
    requires_db: Requiere base de datos

# Configuración de logging
log_cli = true
log_cli_level = INFO
```

## 📝 Escribir Nuevos Tests

### Template para test unitario:

```python
import pytest

def test_mi_funcion():
    """Test descripción breve."""
    # Arrange
    input_data = {...}

    # Act
    result = mi_funcion(input_data)

    # Assert
    assert result is not None
    assert result['campo'] == valor_esperado
```

### Template para test con fixtures:

```python
def test_con_database(db_session, sample_data):
    """Test que usa BD."""
    # Usar db_session
    obj = MiModelo(**sample_data)
    db_session.add(obj)
    db_session.commit()

    # Verificar
    result = db_session.query(MiModelo).first()
    assert result is not None
```

### Template para test de integración:

```python
@pytest.mark.slow
@pytest.mark.integration
def test_api_real():
    """Test con API real."""
    client = MiAPIClient()
    result = client.fetch_data()

    assert result is not None
    assert len(result) > 0
```

## 🐛 Debugging Tests

### Ejecutar un test específico:
```bash
pytest tests/test_validators.py::TestPatentamientoValidator::test_patentamiento_valid -v
```

### Con output completo:
```bash
pytest tests/test_validators.py -v -s
```

### Con debugger:
```bash
pytest tests/test_validators.py --pdb
```

### Stop en primera falla:
```bash
pytest tests/ -x
```

## 🚨 CI/CD Integration

Los tests pueden integrarse en GitHub Actions:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --cov=backend
```

## 📚 Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-cov](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://realpython.com/python-testing/)

## 🤝 Contribuir

Al agregar código nuevo:
1. ✅ Escribir tests para nuevas funcionalidades
2. ✅ Mantener cobertura > 60%
3. ✅ Ejecutar `./run_tests.sh coverage` antes de commit
4. ✅ Todos los tests deben pasar antes de merge

## 📞 Soporte

Para problemas con tests:
1. Revisar logs: `pytest tests/ -v -s`
2. Verificar fixtures en `conftest.py`
3. Consultar documentación de Pytest
