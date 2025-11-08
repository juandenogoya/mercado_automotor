#!/bin/bash
# Script para ejecutar scraping DNRPA en Linux/Mac
# Ejecutar: bash ejecutar_scraping.sh

echo "================================================================================"
echo "           SCRAPING DNRPA - PATENTAMIENTOS DE AUTOS"
echo "================================================================================"
echo ""

# Detectar comando Python correcto
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ ERROR: Python no está instalado"
    echo "   Por favor instalar Python desde: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python detectado: $PYTHON_CMD"
echo ""

# Verificar versión de Python
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "   Versión: $PYTHON_VERSION"
echo ""

# Verificar si las dependencias están instaladas
echo "🔍 Verificando dependencias..."
$PYTHON_CMD -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "📦 Instalando dependencias necesarias..."
    $PYTHON_CMD -m pip install requests beautifulsoup4 pandas openpyxl
    echo ""
fi

echo ""
echo "🚀 Ejecutando scraping..."
echo ""
echo "================================================================================"
echo ""

# Ejecutar el script
$PYTHON_CMD scraping_local_dnrpa.py

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "================================================================================"
    echo ""
    echo "✅ ÉXITO: Scraping completado"
    echo "📁 Busca el archivo: patentamientos_2024.xlsx"
else
    echo ""
    echo "================================================================================"
    echo ""
    echo "❌ ERROR: El script terminó con errores"
    echo "   Revisa los mensajes anteriores para más detalles"
    exit 1
fi

echo ""
