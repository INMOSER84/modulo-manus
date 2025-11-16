#!/bin/bash
# 🔬 AUDITORÍA ULTRA PROFUNDA - ENCUENTRA TODO
# Este script analiza hasta el más mínimo detalle del módulo

set -e

MODULE_PATH="/home/baruc/odoo_project/custom_addons/inmoser_service_order"
CONTAINER_ODOO="odoo_project-odoo-1"
CONTAINER_DB="odoo_project-db-1"
DATABASE="odoo_mx"

REPORT_FILE="/tmp/inmoser_ultra_audit_$(date +%s).txt"

log() {
    echo "$1" | tee -a "$REPORT_FILE"
}

log "════════════════════════════════════════════════════════════"
log "🔬 AUDITORÍA ULTRA PROFUNDA DEL MÓDULO INMOSER"
log "════════════════════════════════════════════════════════════"
log ""
log "📅 Fecha: $(date)"
log "📂 Módulo: $MODULE_PATH"
log ""

# ═══════════════════════════════════════════════════════════════
# 1. VERIFICAR LOGS DE ODOO (ERRORES REALES)
# ═══════════════════════════════════════════════════════════════
log "═══════════════════════════════════════════════════════════════"
log "1️⃣ ANALIZANDO LOGS DE ODOO (Últimos 200 líneas)"
log "═══════════════════════════════════════════════════════════════"

docker logs "$CONTAINER_ODOO" --tail 200 > /tmp/odoo_logs.txt 2>&1

# Buscar errores críticos
log ""
log "🔴 ERRORES CRÍTICOS encontrados:"
grep -i "CRITICAL\|ERROR\|Failed\|Traceback" /tmp/odoo_logs.txt | tail -50 | tee -a "$REPORT_FILE" || log "   ✅ No hay errores críticos visibles"

log ""
log "🔍 Errores relacionados con inmoser_service_order:"
grep -i "inmoser" /tmp/odoo_logs.txt | grep -i "error\|critical\|failed\|exception" | tee -a "$REPORT_FILE" || log "   ✅ No hay errores de inmoser"

# ═══════════════════════════════════════════════════════════════
# 2. VERIFICAR SINTAXIS PYTHON DE TODOS LOS ARCHIVOS
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "2️⃣ VERIFICACIÓN DE SINTAXIS PYTHON"
log "═══════════════════════════════════════════════════════════════"

PYTHON_ERROR=0
for py_file in $(find "$MODULE_PATH" -name "*.py" -type f); do
    if ! python3 -m py_compile "$py_file" 2>/dev/null; then
        log "   ❌ ERROR DE SINTAXIS: $py_file"
        python3 -m py_compile "$py_file" 2>&1 | tee -a "$REPORT_FILE"
        PYTHON_ERROR=1
    fi
done

if [ $PYTHON_ERROR -eq 0 ]; then
    log "   ✅ Todos los archivos Python tienen sintaxis válida"
fi

# ═══════════════════════════════════════════════════════════════
# 3. VERIFICAR SINTAXIS XML DE TODOS LOS ARCHIVOS
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "3️⃣ VERIFICACIÓN DE SINTAXIS XML"
log "═══════════════════════════════════════════════════════════════"

XML_ERROR=0
for xml_file in $(find "$MODULE_PATH" -name "*.xml" -type f); do
    if ! xmllint --noout "$xml_file" 2>/dev/null; then
        log "   ❌ ERROR DE SINTAXIS XML: $xml_file"
        xmllint --noout "$xml_file" 2>&1 | tee -a "$REPORT_FILE"
        XML_ERROR=1
    fi
done

if [ $XML_ERROR -eq 0 ]; then
    log "   ✅ Todos los archivos XML tienen sintaxis válida"
fi

# ═══════════════════════════════════════════════════════════════
# 4. VERIFICAR __manifest__.py EN DETALLE
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "4️⃣ ANÁLISIS PROFUNDO DE __manifest__.py"
log "═══════════════════════════════════════════════════════════════"

MANIFEST="${MODULE_PATH}/__manifest__.py"

log ""
log "📄 Contenido completo del __manifest__.py:"
cat "$MANIFEST" | tee -a "$REPORT_FILE"

log ""
log "🔍 Verificando sintaxis del manifest:"
python3 -c "import ast; ast.parse(open('$MANIFEST').read())" 2>&1 | tee -a "$REPORT_FILE" && log "   ✅ Sintaxis válida" || log "   ❌ SINTAXIS INVÁLIDA"

log ""
log "🔍 Verificando estructura del manifest:"
python3 << 'EOF' 2>&1 | tee -a "$REPORT_FILE"
import sys
sys.path.insert(0, '/home/baruc/odoo_project/custom_addons/inmoser_service_order')
try:
    with open('/home/baruc/odoo_project/custom_addons/inmoser_service_order/__manifest__.py') as f:
        manifest = eval(f.read())
    
    print("✅ Manifest evaluado correctamente")
    print(f"   - Name: {manifest.get('name')}")
    print(f"   - Version: {manifest.get('version')}")
    print(f"   - Depends: {manifest.get('depends')}")
    print(f"   - Installable: {manifest.get('installable')}")
    print(f"   - Application: {manifest.get('application')}")
    
    # Verificar que todos los archivos en 'data' existan
    print("\n🔍 Verificando archivos declarados en 'data':")
    for data_file in manifest.get('data', []):
        import os
        full_path = f"/home/baruc/odoo_project/custom_addons/inmoser_service_order/{data_file}"
        if os.path.exists(full_path):
            print(f"   ✅ {data_file}")
        else:
            print(f"   ❌ FALTA: {data_file}")
            
except Exception as e:
    print(f"❌ ERROR al evaluar manifest: {e}")
    import traceback
    traceback.print_exc()
EOF

# ═══════════════════════════════════════════════════════════════
# 5. VERIFICAR TODOS LOS IMPORTS
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "5️⃣ VERIFICACIÓN DE IMPORTS EN PYTHON"
log "═══════════════════════════════════════════════════════════════"

log ""
log "📄 Contenido de __init__.py principal:"
cat "${MODULE_PATH}/__init__.py" | tee -a "$REPORT_FILE"

log ""
log "📄 Contenido de models/__init__.py:"
cat "${MODULE_PATH}/models/__init__.py" | tee -a "$REPORT_FILE"

log ""
log "🔍 Verificando que cada modelo importado exista:"
while IFS= read -r line; do
    if [[ "$line" =~ from[[:space:]]+\.[[:space:]]+import[[:space:]]+([a-z_]+) ]]; then
        model="${BASH_REMATCH[1]}"
        if [ -f "${MODULE_PATH}/models/${model}.py" ]; then
            log "   ✅ ${model}.py existe"
        else
            log "   ❌ FALTA: models/${model}.py"
        fi
    fi
done < "${MODULE_PATH}/models/__init__.py"

# ═══════════════════════════════════════════════════════════════
# 6. VERIFICAR DEFINICIÓN DE MODELOS (_name, _inherit)
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "6️⃣ ANÁLISIS DE DEFINICIÓN DE MODELOS"
log "═══════════════════════════════════════════════════════════════"

for py_file in $(find "$MODULE_PATH/models" -name "*.py" -type f ! -name "__init__.py"); do
    log ""
    log "📄 Analizando: $(basename $py_file)"
    
    # Buscar _name
    if grep -q "_name = " "$py_file"; then
        NAME=$(grep "_name = " "$py_file" | head -1)
        log "   _name: $NAME"
    else
        log "   ⚠️ Sin _name (podría ser herencia)"
    fi
    
    # Buscar _inherit
    if grep -q "_inherit = " "$py_file"; then
        INHERIT=$(grep "_inherit = " "$py_file" | head -1)
        log "   _inherit: $INHERIT"
    fi
    
    # Buscar _description
    if grep -q "_description = " "$py_file"; then
        DESC=$(grep "_description = " "$py_file" | head -1)
        log "   _description: $DESC"
    else
        log "   ⚠️ Sin _description"
    fi
    
    # Contar campos
    FIELD_COUNT=$(grep -c "= fields\." "$py_file" || echo "0")
    log "   Campos definidos: $FIELD_COUNT"
    
    # Listar todos los campos
    if [ $FIELD_COUNT -gt 0 ]; then
        log "   Lista de campos:"
        grep "= fields\." "$py_file" | sed 's/^/      /' | tee -a "$REPORT_FILE"
    fi
done

# ═══════════════════════════════════════════════════════════════
# 7. VERIFICAR REFERENCIAS ENTRE MODELOS
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "7️⃣ VERIFICACIÓN DE REFERENCIAS ENTRE MODELOS"
log "═══════════════════════════════════════════════════════════════"

log ""
log "🔍 Buscando Many2one que referencien modelos inexistentes:"
for py_file in $(find "$MODULE_PATH/models" -name "*.py" -type f ! -name "__init__.py"); do
    # Buscar Many2one y extraer el modelo referenciado
    grep "Many2one(" "$py_file" | while IFS= read -r line; do
        if [[ "$line" =~ Many2one\([\'\"](.*?)[\'\"] ]]; then
            referenced_model="${BASH_REMATCH[1]}"
            log "   $(basename $py_file): Many2one('$referenced_model')"
        fi
    done
done

log ""
log "🔍 Buscando One2many que referencien modelos inexistentes:"
for py_file in $(find "$MODULE_PATH/models" -name "*.py" -type f ! -name "__init__.py"); do
    grep "One2many(" "$py_file" | while IFS= read -r line; do
        if [[ "$line" =~ One2many\([\'\"](.*?)[\'\"] ]]; then
            referenced_model="${BASH_REMATCH[1]}"
            log "   $(basename $py_file): One2many('$referenced_model')"
        fi
    done
done

# ═══════════════════════════════════════════════════════════════
# 8. VERIFICAR CSV DE SEGURIDAD
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "8️⃣ ANÁLISIS DEL CSV DE SEGURIDAD"
log "═══════════════════════════════════════════════════════════════"

CSV_FILE="${MODULE_PATH}/security/ir.model.access.csv"
log ""
log "📄 Contenido completo del CSV:"
cat "$CSV_FILE" | tee -a "$REPORT_FILE"

log ""
log "🔍 Verificando referencias en el CSV:"
tail -n +2 "$CSV_FILE" | while IFS=',' read -r id name model_id group_id perm_read perm_write perm_create perm_unlink; do
    # Verificar que el modelo exista
    model_name=$(echo "$model_id" | sed 's/model_//' | sed 's/_/./g')
    log "   Acceso: $name → Modelo: $model_name"
    
    # Verificar que el grupo exista
    if [ -n "$group_id" ]; then
        log "      Grupo: $group_id"
    fi
done

# ═══════════════════════════════════════════════════════════════
# 9. VERIFICAR DATOS XML
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "9️⃣ ANÁLISIS DE DATOS XML"
log "═══════════════════════════════════════════════════════════════"

for xml_file in $(find "$MODULE_PATH/data" -name "*.xml" -type f 2>/dev/null); do
    log ""
    log "📄 Analizando: $(basename $xml_file)"
    log "   Contenido completo:"
    cat "$xml_file" | tee -a "$REPORT_FILE"
    
    # Contar registros
    RECORD_COUNT=$(grep -c "<record" "$xml_file" || echo "0")
    log "   Registros definidos: $RECORD_COUNT"
done

# ═══════════════════════════════════════════════════════════════
# 10. VERIFICAR ESTADO EN BASE DE DATOS
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "🔟 ESTADO EN BASE DE DATOS"
log "═══════════════════════════════════════════════════════════════"

log ""
log "1️⃣ Estado del módulo:"
docker exec -i "$CONTAINER_DB" psql -U odoo -d "$DATABASE" -c "
SELECT name, state, latest_version, installed_version
FROM ir_module_module 
WHERE name = 'inmoser_service_order';
" 2>&1 | tee -a "$REPORT_FILE"

log ""
log "2️⃣ Modelos registrados de inmoser:"
docker exec -i "$CONTAINER_DB" psql -U odoo -d "$DATABASE" -c "
SELECT model, name, info
FROM ir_model 
WHERE model LIKE 'inmoser%';
" 2>&1 | tee -a "$REPORT_FILE"

log ""
log "3️⃣ Vistas registradas de inmoser:"
docker exec -i "$CONTAINER_DB" psql -U odoo -d "$DATABASE" -c "
SELECT name, model, type
FROM ir_ui_view 
WHERE name LIKE '%inmoser%';
" 2>&1 | tee -a "$REPORT_FILE"

log ""
log "4️⃣ Registros de datos de inmoser.service.type:"
docker exec -i "$CONTAINER_DB" psql -U odoo -d "$DATABASE" -c "
SELECT * FROM inmoser_service_type;
" 2>&1 | tee -a "$REPORT_FILE" || log "   ⚠️ Tabla aún no existe"

# ═══════════════════════════════════════════════════════════════
# 11. PROBAR IMPORTACIÓN MANUAL
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "1️⃣1️⃣ PRUEBA DE IMPORTACIÓN MANUAL"
log "═══════════════════════════════════════════════════════════════"

log ""
log "🔍 Intentando importar el módulo manualmente:"
python3 << 'EOF' 2>&1 | tee -a "$REPORT_FILE"
import sys
sys.path.insert(0, '/home/baruc/odoo_project/custom_addons/inmoser_service_order')

print("Intentando importar __init__.py...")
try:
    import __init__ as main_init
    print("✅ __init__.py importado correctamente")
except Exception as e:
    print(f"❌ ERROR al importar __init__.py: {e}")
    import traceback
    traceback.print_exc()

print("\nIntentando importar models/__init__.py...")
try:
    from models import __init__ as models_init
    print("✅ models/__init__.py importado correctamente")
except Exception as e:
    print(f"❌ ERROR al importar models/__init__.py: {e}")
    import traceback
    traceback.print_exc()

print("\nIntentando importar cada modelo individualmente...")
models = [
    'inmoser_service_type',
    'inmoser_service_equipment',
    'inmoser_service_specialty',
    'inmoser_service_order',
    'inmoser_service_order_refaction_line'
]

for model in models:
    try:
        exec(f"from models import {model}")
        print(f"✅ {model} importado correctamente")
    except Exception as e:
        print(f"❌ ERROR al importar {model}: {e}")
        import traceback
        traceback.print_exc()
EOF

# ═══════════════════════════════════════════════════════════════
# 12. BUSCAR ARCHIVOS .pyc O CACHE CORRUPTOS
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "1️⃣2️⃣ BÚSQUEDA DE CACHE CORRUPTO"
log "═══════════════════════════════════════════════════════════════"

log ""
log "🔍 Archivos __pycache__ encontrados:"
find "$MODULE_PATH" -type d -name "__pycache__" | tee -a "$REPORT_FILE" || log "   ✅ No hay cache"

log ""
log "🔍 Archivos .pyc encontrados:"
find "$MODULE_PATH" -name "*.pyc" | tee -a "$REPORT_FILE" || log "   ✅ No hay archivos .pyc"

# ═══════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════
log ""
log "═══════════════════════════════════════════════════════════════"
log "📊 RESUMEN DE AUDITORÍA ULTRA PROFUNDA"
log "═══════════════════════════════════════════════════════════════"

TOTAL_ERRORS=0

if [ $PYTHON_ERROR -eq 1 ]; then
    log "❌ ERRORES DE SINTAXIS PYTHON ENCONTRADOS"
    ((TOTAL_ERRORS++))
fi

if [ $XML_ERROR -eq 1 ]; then
    log "❌ ERRORES DE SINTAXIS XML ENCONTRADOS"
    ((TOTAL_ERRORS++))
fi

log ""
log "Total de errores críticos encontrados: $TOTAL_ERRORS"
log ""
log "═══════════════════════════════════════════════════════════════"
log "📄 Reporte completo guardado en: $REPORT_FILE"
log "═══════════════════════════════════════════════════════════════"

# Mostrar el reporte en pantalla también
echo ""
echo "════════════════════════════════════════════════════════════"
echo "📄 MOSTRANDO REPORTE COMPLETO:"
echo "════════════════════════════════════════════════════════════"
cat "$REPORT_FILE"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ AUDITORÍA COMPLETADA"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📝 Para ver el reporte completo:"
echo "   cat $REPORT_FILE"
echo ""
