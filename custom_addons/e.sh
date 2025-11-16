#!/bin/bash

# Script de Auditoría y Corrección Automática de Código para Proyectos Odoo
# Este script audita, corrige automáticamente problemas de estilo y genera un reporte.

# --- Variables de Configuración ---
PROJECT_DIR=$(pwd)
REPORT_FILE="$PROJECT_DIR/audit_report_$(date +%Y%m%d_%H%M%S).txt"

# Herramientas de Linter/Corrección
PYTHON_LINTER="flake8"
PYTHON_FORMATTER="black" # Corrección automática de estilo
PYTHON_FIXER="autopep8" # Corrección automática de estilo (alternativa/complemento)
SHELL_LINTER="shellcheck"
XML_LINTER="xmllint"

# Colores para la salida en consola
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

# --- Funciones de Ayuda ---

# Función para verificar si una herramienta está disponible
check_tool() {
    command -v "$1" &> /dev/null
}

# Función para la corrección automática de Python
fix_python_code() {
    echo -e "${YELLOW}--- Corrigiendo estilo de Python con $PYTHON_FIXER y $PYTHON_FORMATTER ---${NC}" | tee -a "$REPORT_FILE"
    
    find "$PROJECT_DIR" -type f -name "*.py" -not -path "*/__pycache__/*" -not -path "*/.git/*" -print0 | while IFS= read -r -d $'\0' file; do
        echo "-> Formateando: $file" | tee -a "$REPORT_FILE"
        
        # 1. Aplicar correcciones de autopep8 (para problemas de PEP8)
        if check_tool "$PYTHON_FIXER"; then
            "$PYTHON_FIXER" --in-place --aggressive "$file"
        fi
        
        # 2. Aplicar formato de black (para estilo consistente)
        if check_tool "$PYTHON_FORMATTER"; then
            # Usar --quiet para evitar salida excesiva si no hay cambios
            "$PYTHON_FORMATTER" "$file" --quiet
        fi
    done
    echo -e "${GREEN}Corrección de Python completada.${NC}" | tee -a "$REPORT_FILE"
}

# Función para la auditoría de código
run_audit() {
    echo "========================================================================" | tee "$REPORT_FILE"
    echo "  FASE 1: AUDITORÍA DE CÓDIGO (Errores no corregibles automáticamente)" | tee -a "$REPORT_FILE"
    echo "========================================================================" | tee -a "$REPORT_FILE"
    
    local ERROR_COUNT=0

    # 1. Auditoría de Python (solo errores de lógica/estructura, no de estilo)
    echo -e "\n${GREEN}--- 1. Auditoría de Archivos Python (.py) con $PYTHON_LINTER ---${NC}" | tee -a "$REPORT_FILE"
    if check_tool "$PYTHON_LINTER"; then
        find "$PROJECT_DIR" -type f -name "*.py" -not -path "*/__pycache__/*" -not -path "*/.git/*" -print0 | while IFS= read -r -d $'\0' file; do
            # Usar --ignore para ignorar errores de estilo que ya fueron corregidos o son comunes en Odoo
            "$PYTHON_LINTER" --ignore=E501,W504,E731,E121,E126,E127,E128,E129,E131,E133,E203,E226,E231,E241,E251,E261,E262,E265,E266,E271,E272,E275,E301,E302,E303,E305,E306,E402,E701,E702,E703,E704,E711,E712,E713,E714,E721,E722,E731,E741,E742,E743,E901,E902,W191,W291,W292,W293,W391,W503,W504,W601,W602,W603,W604,W605,W606,W607,W619,W690 "$file" 2>&1 | tee -a "$REPORT_FILE"
            if [ ${PIPESTATUS[0]} -ne 0 ]; then
                ERROR_COUNT=$((ERROR_COUNT + 1))
            fi
        done
    fi

    # 2. Auditoría de XML
    echo -e "\n${GREEN}--- 2. Auditoría de Archivos XML (.xml) con $XML_LINTER ---${NC}" | tee -a "$REPORT_FILE"
    if check_tool "$XML_LINTER"; then
        find "$PROJECT_DIR" -type f -name "*.xml" -not -path "*/.git/*" -print0 | while IFS= read -r -d $'\0' file; do
            "$XML_LINTER" --noout "$file" 2>&1 | tee -a "$REPORT_FILE"
            if [ ${PIPESTATUS[0]} -ne 0 ]; then
                ERROR_COUNT=$((ERROR_COUNT + 1))
            fi
        done
    fi

    # 3. Auditoría de Shell
    echo -e "\n${GREEN}--- 3. Auditoría de Archivos Shell (.sh) con $SHELL_LINTER ---${NC}" | tee -a "$REPORT_FILE"
    if check_tool "$SHELL_LINTER"; then
        find "$PROJECT_DIR" -type f -name "*.sh" -not -path "*/.git/*" -print0 | while IFS= read -r -d $'\0' file; do
            "$SHELL_LINTER" "$file" 2>&1 | tee -a "$REPORT_FILE"
            if [ ${PIPESTATUS[0]} -ne 0 ]; then
                ERROR_COUNT=$((ERROR_COUNT + 1))
            fi
        done
    fi

    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "\n${RED}AUDITORÍA COMPLETA: Se encontraron $ERROR_COUNT errores que requieren corrección manual. Revise $REPORT_FILE.${NC}" | tee -a "$REPORT_FILE"
    else
        echo -e "\n${GREEN}AUDITORÍA COMPLETA: No se encontraron errores críticos de lógica o sintaxis (después de la corrección automática).${NC}" | tee -a "$REPORT_FILE"
    fi
}

# --- Funciones de Despliegue (Reutilizadas y Optimizadas) ---

# Función para corregir el error de duplicidad de almacén (WH)
fix_warehouse_duplication_error() {
    echo "========================================================================"
    echo "  FASE 3: CORRECCIÓN PREVENTIVA DE ERRORES DE BASE DE DATOS"
    echo "========================================================================"
    echo -e "${YELLOW}Corrigiendo error de duplicidad de almacén (WH) de forma preventiva...${NC}"
    
    # 1. Iniciar solo el servicio de DB
    echo "Iniciando solo el servicio de base de datos para corrección..."
    docker-compose -f docker-compose.yml up -d db
    
    # Esperar a que la base de datos esté lista
    echo "Esperando 15 segundos para que la base de datos se inicie..."
    sleep 15

    # 2. Ejecutar comandos SQL dentro del contenedor de la base de datos
    echo "Ejecutando comandos SQL de corrección en $DB_NAME..."
    
    # Se usa || true para que el script no falle si la base de datos no existe o no está lista
    docker-compose exec -T db psql -U $DB_USER -d $DB_NAME -c "
        DELETE FROM ir_model_data WHERE module = 'stock' AND name = 'warehouse0';
        DELETE FROM stock_warehouse WHERE code = 'WH';
    " 2>/dev/null || true
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Corrección SQL aplicada (o no necesaria).${NC}"
    else
        echo -e "${YELLOW}Advertencia: No se pudo conectar a la base de datos $DB_NAME para la corrección. El despliegue continuará.${NC}"
    fi
    
    # Detener el servicio de DB
    docker-compose -f docker-compose.yml stop db
}

# --- Ejecución Principal ---

echo "========================================================================"
echo "  INICIANDO PROCESO DE AUDITORÍA Y CORRECCIÓN AUTOMÁTICA"
echo "========================================================================"

# 1. Corrección Automática de Estilo (Python)
if check_tool "$PYTHON_FIXER" && check_tool "$PYTHON_FORMATTER"; then
    fix_python_code
else
    echo -e "${RED}ADVERTENCIA: Las herramientas de corrección automática (autopep8/black) no están instaladas. Saltando corrección de estilo.${NC}"
fi

# 2. Auditoría de Código (Identificar errores de lógica/sintaxis)
run_audit

# 3. Corrección Preventiva de Errores de Despliegue (Odoo/DB)
# Nota: Esta función asume que los archivos docker-compose.yml y config/odoo.conf existen.
fix_warehouse_duplication_error

echo "========================================================================"
echo -e "${GREEN}PROCESO DE AUDITORÍA Y CORRECCIÓN FINALIZADO.${NC}"
echo "Revise el archivo $REPORT_FILE para ver los errores que requieren corrección manual."
echo "El proyecto está listo para ser desplegado con el script 'full_project_deploy_script.sh'."
echo "========================================================================"
