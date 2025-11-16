#!/bin/bash
# Script de Auditoría Completa para Proyecto Odoo
# Ejecutar desde: ~/odoo_project

echo "=========================================="
echo "AUDITORÍA COMPLETA - PROYECTO ODOO"
echo "=========================================="
echo ""

# Crear directorio para reportes
mkdir -p audit_reports
REPORT_DIR="audit_reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ==========================================
# 1. INFORMACIÓN GENERAL DEL PROYECTO
# ==========================================
echo "1. RECOPILANDO INFORMACIÓN GENERAL..."
{
    echo "=== INFORMACIÓN GENERAL DEL PROYECTO ==="
    echo "Fecha de auditoría: $(date)"
    echo ""
    echo "--- Estructura de directorios ---"
    tree -L 3 -d
    echo ""
    echo "--- Tamaño total del proyecto ---"
    du -sh .
    echo ""
    echo "--- Distribución de tamaño por directorio ---"
    du -sh */ 2>/dev/null | sort -hr
} > "$REPORT_DIR/01_info_general_$TIMESTAMP.txt"

# ==========================================
# 2. ANÁLISIS DE MÓDULOS PERSONALIZADOS
# ==========================================
echo "2. ANALIZANDO MÓDULOS PERSONALIZADOS..."
{
    echo "=== ANÁLISIS DE MÓDULOS PERSONALIZADOS ==="
    echo ""
    echo "--- Módulos en custom_addons ---"
    find custom_addons -name "__manifest__.py" -o -name "__openerp__.py"
    echo ""
    echo "--- Contenido de manifiestos ---"
    for manifest in $(find custom_addons -name "__manifest__.py" -o -name "__openerp__.py"); do
        echo "
=== $manifest ==="
        cat "$manifest"
    done
    echo ""
    echo "--- Estadísticas de código Python ---"
    find custom_addons -name "*.py" -type f | xargs wc -l | sort -nr
    echo ""
    echo "--- Modelos definidos ---"
    grep -r "class.*models\.Model" custom_addons --include="*.py"
} > "$REPORT_DIR/02_modulos_custom_$TIMESTAMP.txt"

# ==========================================
# 3. ANÁLISIS DE DEPENDENCIAS
# ==========================================
echo "3. ANALIZANDO DEPENDENCIAS..."
{
    echo "=== ANÁLISIS DE DEPENDENCIAS ==="
    echo ""
    echo "--- requirements.txt principal ---"
    cat requirements.txt
    echo ""
    echo "--- Dependencias en módulos OCA ---"
    find oca_addons -name "requirements.txt" -exec echo "
=== {} ===" \; -exec cat {} \;
    echo ""
    echo "--- Dependencias declaradas en manifiestos ---"
    grep -r "depends" custom_addons --include="__manifest__.py" -A 5
} > "$REPORT_DIR/03_dependencias_$TIMESTAMP.txt"

# ==========================================
# 4. ANÁLISIS DE SEGURIDAD
# ==========================================
echo "4. ANALIZANDO CONFIGURACIÓN DE SEGURIDAD..."
{
    echo "=== ANÁLISIS DE SEGURIDAD ==="
    echo ""
    echo "--- Archivos de seguridad en custom_addons ---"
    find custom_addons -path "*/security/*" -type f
    echo ""
    echo "--- Reglas de acceso (ir.model.access.csv) ---"
    find custom_addons -name "ir.model.access.csv" -exec echo "
=== {} ===" \; -exec cat {} \;
    echo ""
    echo "--- Reglas de registro (ir.rule) ---"
    find custom_addons -name "*security*.xml" -exec echo "
=== {} ===" \; -exec cat {} \;
    echo ""
    echo "--- Grupos de seguridad definidos ---"
    grep -r "res.groups" custom_addons --include="*.xml" --include="*.csv"
} > "$REPORT_DIR/04_seguridad_$TIMESTAMP.txt"

# ==========================================
# 5. ANÁLISIS DE VISTAS Y UI
# ==========================================
echo "5. ANALIZANDO VISTAS Y UI..."
{
    echo "=== ANÁLISIS DE VISTAS Y UI ==="
    echo ""
    echo "--- Archivos de vistas ---"
    find custom_addons -path "*/views/*" -type f
    echo ""
    echo "--- Tipos de vistas definidas ---"
    grep -r "<field name=\"arch\"" custom_addons --include="*.xml" | grep -o "type=\"[^\"]*\"" | sort | uniq -c
    echo ""
    echo "--- Menús definidos ---"
    grep -r "<menuitem" custom_addons --include="*.xml"
    echo ""
    echo "--- Assets estáticos ---"
    find custom_addons -path "*/static/*" -type f
} > "$REPORT_DIR/05_vistas_ui_$TIMESTAMP.txt"

# ==========================================
# 6. ANÁLISIS DE DATOS Y FIXTURES
# ==========================================
echo "6. ANALIZANDO DATOS Y FIXTURES..."
{
    echo "=== ANÁLISIS DE DATOS Y FIXTURES ==="
    echo ""
    echo "--- Archivos de datos ---"
    find custom_addons -path "*/data/*" -type f
    echo ""
    echo "--- Datos demo ---"
    grep -r "demo.*:" custom_addons --include="__manifest__.py" -A 3
    echo ""
    echo "--- Datos de inicialización ---"
    grep -r "data.*:" custom_addons --include="__manifest__.py" -A 5
} > "$REPORT_DIR/06_datos_$TIMESTAMP.txt"

# ==========================================
# 7. ANÁLISIS DE PRUEBAS
# ==========================================
echo "7. ANALIZANDO PRUEBAS..."
{
    echo "=== ANÁLISIS DE PRUEBAS ==="
    echo ""
    echo "--- Archivos de test ---"
    find custom_addons -path "*/tests/*" -type f
    echo ""
    echo "--- Clases de test ---"
    grep -r "class.*TransactionCase\|class.*SingleTransactionCase" custom_addons --include="*.py"
    echo ""
    echo "--- Métodos de test ---"
    grep -r "def test_" custom_addons --include="*.py" | wc -l
    echo " métodos de test encontrados"
} > "$REPORT_DIR/07_pruebas_$TIMESTAMP.txt"

# ==========================================
# 8. ANÁLISIS DE CONFIGURACIÓN
# ==========================================
echo "8. ANALIZANDO CONFIGURACIÓN..."
{
    echo "=== ANÁLISIS DE CONFIGURACIÓN ==="
    echo ""
    echo "--- odoo.conf ---"
    cat config/odoo.conf
    echo ""
    echo "--- odoo.conf (raíz) ---"
    if [ -f odoo.conf ]; then
        cat odoo.conf
    fi
    echo ""
    echo "--- docker-compose.yml ---"
    cat docker-compose.yml
} > "$REPORT_DIR/08_configuracion_$TIMESTAMP.txt"

# ==========================================
# 9. ANÁLISIS DE CALIDAD DE CÓDIGO
# ==========================================
echo "9. ANALIZANDO CALIDAD DE CÓDIGO..."
{
    echo "=== ANÁLISIS DE CALIDAD DE CÓDIGO ==="
    echo ""
    echo "--- Archivos Python sin __init__.py ---"
    find custom_addons -type d -exec sh -c '[ ! -f "$1/__init__.py" ] && [ -n "$(find "$1" -maxdepth 1 -name "*.py" -type f)" ] && echo "$1"' _ {} \;
    echo ""
    echo "--- Importaciones problemáticas ---"
    grep -r "from.*import \*" custom_addons --include="*.py"
    echo ""
    echo "--- TODO y FIXME en el código ---"
    grep -rn "TODO\|FIXME\|XXX\|HACK" custom_addons --include="*.py"
    echo ""
    echo "--- Strings hardcodeados (posibles traducciones faltantes) ---"
    grep -rn "string=" custom_addons --include="*.py" | head -50
    echo ""
    echo "--- Funciones muy largas (>100 líneas) ---"
    find custom_addons -name "*.py" -exec awk '/^[[:space:]]*def /{f=1; name=$0; line=NR; count=0} f{count++} /^[[:space:]]*def |^class |^$/{if(f && count>100) print FILENAME":"line":"name" ("count" líneas)"; f=0}' {} \;
} > "$REPORT_DIR/09_calidad_codigo_$TIMESTAMP.txt"

# ==========================================
# 10. ANÁLISIS DE BASE DE DATOS
# ==========================================
echo "10. PREPARANDO ANÁLISIS DE BASE DE DATOS..."
{
    echo "=== ANÁLISIS DE BASE DE DATOS ==="
    echo ""
    echo "--- Modelos con campos computados ---"
    grep -r "compute=" custom_addons --include="*.py" | wc -l
    echo " campos computados encontrados"
    echo ""
    echo "--- Modelos con campos relacionados ---"
    grep -r "related=" custom_addons --include="*.py" | wc -l
    echo " campos relacionados encontrados"
    echo ""
    echo "--- Constraints SQL ---"
    grep -r "_sql_constraints" custom_addons --include="*.py" -A 3
    echo ""
    echo "--- Constraints Python ---"
    grep -r "@api.constrains" custom_addons --include="*.py" -A 2
} > "$REPORT_DIR/10_base_datos_$TIMESTAMP.txt"

# ==========================================
# 11. ANÁLISIS DE RENDIMIENTO
# ==========================================
echo "11. ANALIZANDO POSIBLES PROBLEMAS DE RENDIMIENTO..."
{
    echo "=== ANÁLISIS DE RENDIMIENTO ==="
    echo ""
    echo "--- Bucles potencialmente problemáticos ---"
    grep -rn "for.*in.*self\." custom_addons --include="*.py" | head -50
    echo ""
    echo "--- Búsquedas sin límite ---"
    grep -rn "\.search\(" custom_addons --include="*.py" | grep -v "limit=" | head -50
    echo ""
    echo "--- Acceso a campos relacionados en bucles ---"
    grep -rn "for.*\..*\." custom_addons --include="*.py" | head -30
} > "$REPORT_DIR/11_rendimiento_$TIMESTAMP.txt"

# ==========================================
# 12. ANÁLISIS DE MÓDULOS OCA
# ==========================================
echo "12. ANALIZANDO MÓDULOS OCA INSTALADOS..."
{
    echo "=== ANÁLISIS DE MÓDULOS OCA ==="
    echo ""
    echo "--- Repositorios OCA ---"
    ls -la oca_addons/
    echo ""
    echo "--- Número de módulos por repositorio ---"
    for repo in oca_addons/*/; do
        if [ -d "$repo" ]; then
            count=$(find "$repo" -name "__manifest__.py" -o -name "__openerp__.py" | wc -l)
            echo "$(basename $repo): $count módulos"
        fi
    done
    echo ""
    echo "--- Verificación de archivos README ---"
    find oca_addons -name "README.md" -o -name "README.rst" | head -20
} > "$REPORT_DIR/12_modulos_oca_$TIMESTAMP.txt"

# ==========================================
# 13. ANÁLISIS DE WIZARDS
# ==========================================
echo "13. ANALIZANDO WIZARDS..."
{
    echo "=== ANÁLISIS DE WIZARDS ==="
    echo ""
    echo "--- Archivos de wizards ---"
    find custom_addons -path "*/wizards/*" -type f
    echo ""
    echo "--- Modelos TransientModel ---"
    grep -r "models.TransientModel" custom_addons --include="*.py" -B 1
} > "$REPORT_DIR/13_wizards_$TIMESTAMP.txt"

# ==========================================
# 14. BÚSQUEDA DE PROBLEMAS COMUNES
# ==========================================
echo "14. BUSCANDO PROBLEMAS COMUNES..."
{
    echo "=== BÚSQUEDA DE PROBLEMAS COMUNES ==="
    echo ""
    echo "--- Archivos con permisos incorrectos ---"
    find custom_addons -type f -executable -name "*.py" -o -name "*.xml" -o -name "*.csv"
    echo ""
    echo "--- Archivos de respaldo o temporales ---"
    find . -name "*.pyc" -o -name "*.pyo" -o -name "*~" -o -name "*.bak" -o -name "*.swp"
    echo ""
    echo "--- Archivos Zone.Identifier (Windows) ---"
    find . -name "*:Zone.Identifier"
    echo ""
    echo "--- Posibles credenciales hardcodeadas ---"
    grep -rni "password\s*=\|pwd\s*=\|passwd\s*=" custom_addons --include="*.py" --include="*.xml" | grep -v "context\|field"
    echo ""
    echo "--- URLs hardcodeadas ---"
    grep -rn "http://\|https://" custom_addons --include="*.py" | head -30
} > "$REPORT_DIR/14_problemas_comunes_$TIMESTAMP.txt"

# ==========================================
# 15. RESUMEN EJECUTIVO
# ==========================================
echo "15. GENERANDO RESUMEN EJECUTIVO..."
{
    echo "=== RESUMEN EJECUTIVO DE AUDITORÍA ==="
    echo "Fecha: $(date)"
    echo ""
    echo "--- ESTADÍSTICAS GENERALES ---"
    echo "Tamaño total del proyecto: $(du -sh . | cut -f1)"
    echo "Módulos personalizados: $(find custom_addons -name "__manifest__.py" | wc -l)"
    echo "Repositorios OCA: $(ls -d oca_addons/*/ 2>/dev/null | wc -l)"
    echo "Archivos Python en custom_addons: $(find custom_addons -name "*.py" | wc -l)"
    echo "Archivos XML en custom_addons: $(find custom_addons -name "*.xml" | wc -l)"
    echo "Líneas de código Python: $(find custom_addons -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}')"
    echo ""
    echo "--- ARCHIVOS DE CONFIGURACIÓN ---"
    echo "✓ docker-compose.yml existe"
    echo "✓ config/odoo.conf existe"
    echo "✓ requirements.txt existe"
    echo ""
    echo "--- ÁREAS DE ATENCIÓN ---"
    echo "• Revisar TODOs y FIXMEs: $(grep -r "TODO\|FIXME" custom_addons --include="*.py" | wc -l) encontrados"
    echo "• Archivos temporales: $(find . -name "*.pyc" -o -name "*~" | wc -l) encontrados"
    echo "• Zone.Identifier files: $(find . -name "*:Zone.Identifier" | wc -l) encontrados"
    echo ""
    echo "--- SIGUIENTE PASO ---"
    echo "Revisar los reportes individuales en: $REPORT_DIR/"
} > "$REPORT_DIR/00_resumen_ejecutivo_$TIMESTAMP.txt"

# ==========================================
# FINALIZACIÓN
# ==========================================
echo ""
echo "=========================================="
echo "AUDITORÍA COMPLETADA"
echo "=========================================="
echo ""
echo "Los reportes han sido generados en: $REPORT_DIR/"
echo ""
echo "Archivos generados:"
ls -lh "$REPORT_DIR"/*$TIMESTAMP.txt
echo ""
echo "Para ver el resumen ejecutivo:"
echo "cat $REPORT_DIR/00_resumen_ejecutivo_$TIMESTAMP.txt"
echo ""
