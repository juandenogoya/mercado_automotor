#!/bin/bash
# ============================================================================
# Setup Script - ETL SIOGRANOS
# ============================================================================
# Configura base de datos y archivos necesarios para ETL SIOGRANOS
# ============================================================================

set -e  # Exit on error

echo "================================================================================"
echo "🌾 SETUP - ETL SIOGRANOS"
echo "================================================================================"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================================================
# 1. Verificar PostgreSQL
# ============================================================================
echo ""
echo "📦 Verificando PostgreSQL..."

if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL no está instalado${NC}"
    echo "Instala PostgreSQL: https://www.postgresql.org/download/"
    exit 1
fi

echo -e "${GREEN}✅ PostgreSQL encontrado${NC}"
psql --version

# ============================================================================
# 2. Verificar Python y dependencias
# ============================================================================
echo ""
echo "🐍 Verificando Python..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python encontrado${NC}"
python3 --version

# ============================================================================
# 3. Instalar dependencias Python
# ============================================================================
echo ""
echo "📥 Instalando dependencias Python..."

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ No se encontró requirements.txt${NC}"
    exit 1
fi

pip install -q requests psycopg2-binary python-dotenv tabulate

echo -e "${GREEN}✅ Dependencias instaladas${NC}"

# ============================================================================
# 4. Configurar .env si no existe
# ============================================================================
echo ""
echo "⚙️  Configurando variables de entorno..."

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Archivo .env no existe. Creando plantilla...${NC}"

    cat > .env << 'EOF'
# PostgreSQL Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mercado_automotor
DB_USER=postgres
DB_PASSWORD=

# SIOGRANOS API
# NOTA: Cambiar a URL de producción cuando esté disponible
SIOGRANOS_API_URL=https://test.bc.org.ar/SiogranosAPI/api/ConsultaPublica/consultarOperaciones
EOF

    echo -e "${GREEN}✅ Archivo .env creado${NC}"
    echo -e "${YELLOW}⚠️  EDITA .env y configura tu DB_PASSWORD${NC}"
    echo ""
    read -p "Presiona Enter cuando hayas configurado .env..."
else
    echo -e "${GREEN}✅ Archivo .env ya existe${NC}"
fi

# Cargar variables de .env
source .env

# ============================================================================
# 5. Verificar/Crear base de datos
# ============================================================================
echo ""
echo "🗄️  Configurando base de datos..."

# Verificar si la base de datos existe
DB_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✅ Base de datos '$DB_NAME' ya existe${NC}"
else
    echo -e "${YELLOW}📦 Creando base de datos '$DB_NAME'...${NC}"
    PGPASSWORD=$DB_PASSWORD createdb -h $DB_HOST -U $DB_USER $DB_NAME
    echo -e "${GREEN}✅ Base de datos creada${NC}"
fi

# ============================================================================
# 6. Crear schema y tablas
# ============================================================================
echo ""
echo "📋 Creando tablas..."

if [ ! -f "database/schemas/siogranos_schema.sql" ]; then
    echo -e "${RED}❌ No se encontró database/schemas/siogranos_schema.sql${NC}"
    exit 1
fi

# Verificar si las tablas ya existen
TABLE_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='siogranos_operaciones'" 2>/dev/null || echo "0")

if [ "$TABLE_EXISTS" = "1" ]; then
    echo -e "${YELLOW}⚠️  Tablas SIOGRANOS ya existen${NC}"
    read -p "¿Recrear tablas? Esto BORRARÁ todos los datos. (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo "🔄 Recreando tablas..."
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f database/schemas/siogranos_schema.sql
        echo -e "${GREEN}✅ Tablas recreadas${NC}"
    else
        echo "Manteniendo tablas existentes"
    fi
else
    echo "📦 Creando tablas por primera vez..."
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f database/schemas/siogranos_schema.sql
    echo -e "${GREEN}✅ Tablas creadas${NC}"
fi

# ============================================================================
# 7. Verificar estructura
# ============================================================================
echo ""
echo "🔍 Verificando estructura..."

TABLE_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'siogranos%'")

echo -e "${GREEN}✅ Tablas SIOGRANOS encontradas: $TABLE_COUNT${NC}"

# Mostrar tablas
echo ""
echo "📋 Tablas creadas:"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt siogranos*"

# ============================================================================
# 8. Test de conectividad API
# ============================================================================
echo ""
echo "🌐 Probando conectividad con API SIOGRANOS..."

if command -v python3 &> /dev/null; then
    python3 -c "
import requests
import sys

try:
    url = '$SIOGRANOS_API_URL'
    response = requests.get(url, timeout=10)
    print(f'✅ API respondió con status: {response.status_code}')
    if response.status_code == 200:
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f'❌ Error al conectar con API: {e}')
    sys.exit(1)
" && echo -e "${GREEN}✅ API accesible${NC}" || echo -e "${YELLOW}⚠️  API no responde (puede ser normal en servidor de testing)${NC}"
fi

# ============================================================================
# RESUMEN
# ============================================================================
echo ""
echo "================================================================================"
echo "📊 RESUMEN DEL SETUP"
echo "================================================================================"
echo ""
echo -e "${GREEN}✅ PostgreSQL: Configurado${NC}"
echo -e "${GREEN}✅ Base de datos: $DB_NAME${NC}"
echo -e "${GREEN}✅ Tablas: Creadas${NC}"
echo -e "${GREEN}✅ Dependencias: Instaladas${NC}"
echo ""
echo "================================================================================"
echo "🚀 PRÓXIMOS PASOS"
echo "================================================================================"
echo ""
echo "1. Verificar configuración:"
echo "   ${YELLOW}python verificar_chunks_siogranos.py${NC}"
echo ""
echo "2. Ejecutar ETL (carga histórica completa):"
echo "   ${YELLOW}python etl_siogranos.py${NC}"
echo ""
echo "   Esto cargará datos desde 2020-01-01 hasta hoy (~296 chunks)"
echo "   Tiempo estimado: 15-30 minutos"
echo ""
echo "3. Monitorear progreso:"
echo "   ${YELLOW}tail -f etl_siogranos.log${NC}"
echo ""
echo "4. Ver estadísticas:"
echo "   ${YELLOW}python verificar_chunks_siogranos.py${NC}"
echo ""
echo "================================================================================"
echo "📚 DOCUMENTACIÓN"
echo "================================================================================"
echo ""
echo "Ver documentación completa en:"
echo "   ${YELLOW}docs/ETL_SIOGRANOS.md${NC}"
echo ""
echo "================================================================================"
echo -e "${GREEN}✅ Setup completado${NC}"
echo "================================================================================"
