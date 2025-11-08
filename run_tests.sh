#!/bin/bash
# Script para ejecutar tests del proyecto Mercado Automotor

set -e  # Exit on error

echo "======================================"
echo "  Mercado Automotor - Test Suite"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que pytest esté instalado
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}ERROR: pytest no está instalado${NC}"
    echo "Instalar con: pip install pytest pytest-cov"
    exit 1
fi

# Función para ejecutar tests
run_tests() {
    local test_type=$1
    local test_args=$2

    echo -e "${YELLOW}Ejecutando: $test_type${NC}"
    echo "----------------------------------------"

    if pytest $test_args; then
        echo -e "${GREEN}✓ $test_type: PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ $test_type: FAILED${NC}"
        return 1
    fi
    echo ""
}

# Menú de opciones
case "${1:-all}" in
    "all")
        echo "Ejecutando TODOS los tests..."
        echo ""
        run_tests "Tests Completos" "tests/ -v --tb=short"
        ;;

    "unit")
        echo "Ejecutando tests UNITARIOS (rápidos)..."
        echo ""
        run_tests "Tests Unitarios" "tests/ -v -m 'not slow and not integration' --tb=short"
        ;;

    "integration")
        echo "Ejecutando tests de INTEGRACIÓN..."
        echo ""
        run_tests "Tests Integración" "tests/ -v -m integration --tb=short"
        ;;

    "coverage")
        echo "Ejecutando tests con COBERTURA..."
        echo ""
        pytest tests/ -v --cov=backend --cov-report=html --cov-report=term-missing --tb=short
        echo ""
        echo -e "${GREEN}Reporte de cobertura generado en: htmlcov/index.html${NC}"
        ;;

    "validators")
        echo "Ejecutando tests de VALIDADORES..."
        echo ""
        run_tests "Validadores" "tests/test_validators.py -v"
        ;;

    "indicadores")
        echo "Ejecutando tests de INDICADORES..."
        echo ""
        run_tests "Indicadores" "tests/test_indicadores.py -v"
        ;;

    "models")
        echo "Ejecutando tests de MODELOS..."
        echo ""
        run_tests "Modelos" "tests/test_models.py -v"
        ;;

    "api")
        echo "Ejecutando tests de API CLIENTS..."
        echo ""
        run_tests "API Clients" "tests/test_api_clients.py -v"
        ;;

    "scrapers")
        echo "Ejecutando tests de SCRAPERS..."
        echo ""
        run_tests "Scrapers" "tests/test_scrapers_real.py -v -m integration"
        ;;

    "quick")
        echo "Ejecutando tests RÁPIDOS (sin integración)..."
        echo ""
        run_tests "Quick Tests" "tests/ -v -m 'not slow' --tb=line -x"
        ;;

    "help")
        echo "Uso: $0 [opción]"
        echo ""
        echo "Opciones:"
        echo "  all          - Ejecutar todos los tests (default)"
        echo "  unit         - Solo tests unitarios (rápidos)"
        echo "  integration  - Solo tests de integración"
        echo "  coverage     - Tests con reporte de cobertura"
        echo "  validators   - Solo tests de validadores"
        echo "  indicadores  - Solo tests de indicadores"
        echo "  models       - Solo tests de modelos"
        echo "  api          - Solo tests de API clients"
        echo "  scrapers     - Solo tests de scrapers (requiere conexión)"
        echo "  quick        - Tests rápidos (para desarrollo)"
        echo "  help         - Mostrar esta ayuda"
        echo ""
        echo "Ejemplos:"
        echo "  $0                  # Ejecutar todos los tests"
        echo "  $0 unit            # Solo tests unitarios"
        echo "  $0 coverage        # Con reporte de cobertura"
        ;;

    *)
        echo -e "${RED}Opción inválida: $1${NC}"
        echo "Usar '$0 help' para ver opciones disponibles"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "  Tests completados"
echo "======================================"
