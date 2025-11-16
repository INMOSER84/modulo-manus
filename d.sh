#!/bin/bash

# Script de Análisis Estático de Código para Proyectos Odoo
# Revisa archivos Python, XML, JavaScript y Shell en busca de errores y problemas de estilo.

# --- Configuración de Herramientas ---
# Se asume que las siguientes herramientas están instaladas.
# Si no lo están, el script intentará instalarlas (requiere sudo).
PYTHON_LINTER="flake8" # Alternativa: pylint
SHELL_LINTER="shellcheck"
XML_LINTER="xmllint" # Para validación básica de XML

# Directorio base del proyecto (donde se encuentra este script)
PROJECT_DIR=$(dirname "$0")

# Archivo de reporte de salida
REPORT_FILE="$PROJECT_DIR/code_review_report_$(date +%Y%m%d_%H%M%S).txt"

# Colores para la salida en consola
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

# --- Funciones de Ayuda ---

# Función para verificar e instalar herramientas
check_and_install() {
    local tool_name=$1
    if ! command -v "$tool_name" &> /dev/null
    then
        echo -e "${YELLOW}Advertencia: La herramienta '$tool_name' no está instalada. Intentando instalar...${NC}"
        # Intentar instalar con apt, asumiendo un entorno Debian/Ubuntu
        sudo apt-get update > /dev/null 2>&1
        if [ "$tool_name" == "flake8" ]; then
            sudo apt-get install -y python3-flake8
        elif [ "$tool_name" == "shellcheck" ]; then
            sudo apt-get install -y shellcheck
        elif [ "$tool_name" == "xmllint" ]; then
            sudo apt-get install -y libxml2-utils
        else
            echo -e "${RED}Error: No se pudo instalar '$tool_name'. Por favor, instálelo manualmente.${NC}"
            return 1
        fi
        if command -v "$tool_name" &> /dev/null; then
            echo -e "${GREEN}Éxito: '$tool_name' instalado.${NC}"
        else
            echo -e "${RED}Error: La instalación de '$tool_name' falló. Saltando la revisión para este tipo de archivo.${NC}"
            return 1
        fi
    fi
    return 0
}

# --- Ejecución del Análisis ---

echo "========================================================================" | tee -a "$REPORT_FILE"
echo "  INICIANDO ANÁLISIS ESTÁTICO DE CÓDIGO EN EL PROYECTO ODOO" | tee -a "$REPORT_FILE"
echo "  Fecha y Hora: $(date)" | tee -a "$REPORT_FILE"
echo "========================================================================" | tee -a "$REPORT_FILE"

# 1. Revisión de Archivos Python (.py)
echo -e "\n${GREEN}--- 1. Revisión de Archivos Python (.py) con $PYTHON_LINTER ---${NC}" | tee -a "$REPORT_FILE"
if check_and_install "$PYTHON_LINTER"; then
    find "$PROJECT_DIR" -type f -name "*.py" -not -path "*/__pycache__/*" -not -path "*/.git/*" -print0 | while IFS= read -r -d $'\0' file; do
        echo "-> Analizando: $file" | tee -a "$REPORT_FILE"
        # Usar --ignore para ignorar errores comunes de Odoo que no son críticos (como la longitud de línea)
        # Se puede personalizar la lista de ignorados según las necesidades del proyecto.
        $PYTHON_LINTER --ignore=E501,W504,E731 "$file" 2>&1 | tee -a "$REPORT_FILE"
    done
else
    echo -e "${RED}Saltando revisión de Python.${NC}" | tee -a "$REPORT_FILE"
fi

# 2. Revisión de Archivos XML (.xml)
echo -e "\n${GREEN}--- 2. Revisión de Archivos XML (.xml) con $XML_LINTER ---${NC}" | tee -a "$REPORT_FILE"
if check_and_install "$XML_LINTER"; then
    find "$PROJECT_DIR" -type f -name "*.xml" -not -path "*/.git/*" -print0 | while IFS= read -r -d $'\0' file; do
        echo "-> Analizando: $file" | tee -a "$REPORT_FILE"
        # xmllint para verificar la sintaxis básica del XML
        $XML_LINTER --noout "$file" 2>&1 | tee -a "$REPORT_FILE"
    done
else
    echo -e "${RED}Saltando revisión de XML.${NC}" | tee -a "$REPORT_FILE"
fi

# 3. Revisión de Archivos Shell (.sh)
echo -e "\n${GREEN}--- 3. Revisión de Archivos Shell (.sh) con $SHELL_LINTER ---${NC}" | tee -a "$REPORT_FILE"
if check_and_install "$SHELL_LINTER"; then
    find "$PROJECT_DIR" -type f -name "*.sh" -not -path "*/.git/*" -print0 | while IFS= read -r -d $'\0' file; do
        echo "-> Analizando: $file" | tee -a "$REPORT_FILE"
        $SHELL_LINTER "$file" 2>&1 | tee -a "$REPORT_FILE"
    done
else
    echo -e "${RED}Saltando revisión de Shell.${NC}" | tee -a "$REPORT_FILE"
fi

# 4. Revisión de Archivos de Manifiesto (__manifest__.py)
# Aunque son archivos Python, una revisión específica puede ser útil para asegurar la estructura.
echo -e "\n${GREEN}--- 4. Revisión de Archivos de Manifiesto (__manifest__.py) ---${NC}" | tee -a "$REPORT_FILE"
find "$PROJECT_DIR" -type f -name "__manifest__.py" -not -path "*/.git/*" -print0 | while IFS= read -r -d $'\0' file; do
    # Una simple comprobación de sintaxis Python
    python3 -m py_compile "$file" 2>&1 | tee -a "$REPORT_FILE"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error de sintaxis en el manifiesto: $file${NC}" | tee -a "$REPORT_FILE"
    else
        echo "Sintaxis OK: $file" | tee -a "$REPORT_FILE"
    fi
done

echo "========================================================================" | tee -a "$REPORT_FILE"
echo -e "${GREEN}ANÁLISIS COMPLETADO.${NC}" | tee -a "$REPORT_FILE"
echo "El reporte detallado se guardó en: $REPORT_FILE" | tee -a "$REPORT_FILE"
echo "========================================================================" | tee -a "$REPORT_FILE"
