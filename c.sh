#!/bin/bash
# ultra_audit_inmoser.sh - Auditoría de todos los códigos del módulo

MODULE_PATH="/home/baruc/odoo_project/custom_addons/inmoser_service_order"
REPORT_FILE="/tmp/inmoser_ultra_audit_$(date +%Y%m%d_%H%M%S).txt"

echo "════════════════════════════════════════════════════════════════" > $REPORT_FILE
echo "  AUDITORÍA ULTRA PROFUNDA - INMOSER SERVICE ORDER" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "Fecha: $(date)" >> $REPORT_FILE
echo "Ruta: $MODULE_PATH" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Contadores
ERRORS=0
WARNINGS=0

# Función para registrar errores
log_error() {
    echo "❌ ERROR: $1" | tee -a $REPORT_FILE
    ((ERRORS++))
}

log_warning() {
    echo "⚠️  WARNING: $1" | tee -a $REPORT_FILE
    ((WARNINGS++))
}

log_success() {
    echo "✅ OK: $1" | tee -a $REPORT_FILE
}

# 1. AUDITORÍA DE ARCHIVOS PYTHON
echo "" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "1. AUDITORÍA DE ARCHIVOS PYTHON" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE

for py_file in $(find $MODULE_PATH -name "*.py" -type f | sort); do
    echo "" >> $REPORT_FILE
    echo "📄 Analizando: $py_file" >> $REPORT_FILE
    
    # Verificar sintaxis
    if python3 -m py_compile "$py_file" 2>/dev/null; then
        log_success "Sintaxis válida: $py_file"
    else
        log_error "Sintaxis inválida: $py_file"
        python3 -m py_compile "$py_file" 2>&1 >> $REPORT_FILE
    fi
    
    # Verificar encoding
    if file "$py_file" | grep -q "ASCII text\|UTF-8 Unicode text"; then
        log_success "Encoding correcto: $py_file"
    else
        log_warning "Encoding problemático: $py_file"
        file "$py_file" >> $REPORT_FILE
    fi
    
    # Verificar imports de Odoo
    while IFS= read -r line; do
        if [[ $line =~ ^from[[:space:]]+odoo ]]; then
            import_name=$(echo "$line" | cut -d' ' -f2)
            log_success "Import de Odoo válido: $import_name"
        fi
    done < "$py_file"
    
    # Verificar definiciones de modelos
    if grep -q "_name.*=" "$py_file"; then
        model_name=$(grep "_name.*=" "$py_file" | head -1 | cut -d"'" -f2 | cut -d'"' -f2)
        log_success "Modelo definido: $model_name en $py_file"
    fi
    
    # Verificar _inherit sin _name (herencia)
    if grep -q "_inherit.*=" "$py_file" && ! grep -q "_name.*=" "$py_file"; then
        inherit_name=$(grep "_inherit.*=" "$py_file" | head -1 | cut -d"'" -f2 | cut -d'"' -f2)
        log_warning "Herencia detectada sin _name: $inherit_name en $py_file"
    fi
    
    # Verificar campos fields. sin importar
    if grep -q "fields\." "$py_file" && ! grep -q "from odoo import.*fields" "$py_file" && ! grep -q "from odoo import.*models" "$py_file"; then
        log_warning "Uso de 'fields.' sin importar models/fields en $py_file"
    fi
    
    # Verificar llamadas a self.env sin contexto
    if grep -q "self\.env\." "$py_file" && ! grep -q "def " "$py_file"; then
        log_warning "Uso de self.env fuera de métodos en $py_file"
    fi
done

# 2. AUDITORÍA DE ARCHIVOS XML
echo "" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "2. AUDITORÍA DE ARCHIVOS XML" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE

for xml_file in $(find $MODULE_PATH -name "*.xml" -type f | sort); do
    echo "" >> $REPORT_FILE
    echo "📄 Analizando: $xml_file" >> $REPORT_FILE
    
    # Verificar sintaxis XML
    if xmllint --noout "$xml_file" 2>/dev/null; then
        log_success "Sintaxis XML válida: $xml_file"
    else
        log_error "Sintaxis XML inválida: $xml_file"
        xmllint --noout "$xml_file" 2>&1 >> $REPORT_FILE
    fi
    
    # Verificar referencias a modelos en records
    grep -o 'model="[^"]*"' "$xml_file" | while read -r model_ref; do
        model_name=$(echo "$model_ref" | cut -d'"' -f2)
        log_success "Referencia a modelo: $model_name en $xml_file"
    done
    
    # Verificar referencias a vistas
    grep -o 'inherit_id="[^"]*"' "$xml_file" | while read -r inherit_ref; do
        inherit_id=$(echo "$inherit_ref" | cut -d'"' -f2)
        log_warning "Herencia de vista: $inherit_id en $xml_file"
    done
    
    # Verificar campos en vistas
    grep -o 'name="[^"]*"' "$xml_file" | grep -v "model\|inherit_id\|id" | while read -r field_ref; do
        field_name=$(echo "$field_ref" | cut -d'"' -f2)
        log_success "Campo en vista: $field_name en $xml_file"
    done
    
    # Verificar botones
    grep -o 'name="[^"]*"' "$xml_file" | grep -E "button|action" | while read -r button_ref; do
        button_name=$(echo "$button_ref" | cut -d'"' -f2)
        log_success "Botón/Acción: $button_name en $xml_file"
    done
done

# 3. AUDITORÍA DE CSV
echo "" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "3. AUDITORÍA DE ARCHIVOS CSV" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE

for csv_file in $(find $MODULE_PATH -name "*.csv" -type f | sort); do
    echo "" >> $REPORT_FILE
    echo "📄 Analizando: $csv_file" >> $REPORT_FILE
    
    # Verificar formato CSV
    if python3 -c "import csv; list(csv.reader(open('$csv_file')))" 2>/dev/null; then
        log_success "Formato CSV válido: $csv_file"
    else
        log_error "Formato CSV inválido: $csv_file"
    fi
    
    # Verificar referencias a modelos
    head -1 "$csv_file" | grep -q "model_id:id" && log_success "Cabecera CSV correcta: $csv_file" || log_error "Cabecera CSV incorrecta: $csv_file"
    
    # Verificar que el modelo existe en el CSV
    tail -n +2 "$csv_file" | while IFS=',' read -r id name model_id group_id perm_read perm_write perm_create perm_unlink; do
        model_name=$(echo "$model_id" | cut -d'.' -f2)
        log_success "Permiso para modelo: $model_name en $csv_file"
    done
done

# 4. VERIFICACIÓN DE COHERENCIA MODELO-VISTA
echo "" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "4. VERIFICACIÓN DE COHERENCIA MODELO-VISTA" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE

# Extraer todos los campos definidos en modelos
ALL_FIELDS=$(grep -r "fields\." $MODULE_PATH/models/ | grep -o "fields\.[A-Za-z_]*" | sort -u)

# Extraer todos los campos usados en vistas
VIEW_FIELDS=$(grep -r 'name="' $MODULE_PATH/views/ | grep -v "model\|inherit_id\|id" | sed 's/.*name="\([^"]*\)".*/\1/' | sort -u)

# Comparar
for field in $VIEW_FIELDS; do
    if echo "$ALL_FIELDS" | grep -q "$field"; then
        log_success "Campo coherente: $field"
    else
        log_warning "Campo en vista pero no en modelo: $field"
    fi
done

# 5. VERIFICACIÓN DE IMPORTS
echo "" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "5. VERIFICACIÓN DE IMPORTS EN __init__.py" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE

# Verificar imports en __init__.py principal
grep "import" $MODULE_PATH/__init__.py | while read -r import_line; do
    if [[ $import_line =~ from\.import(.+) ]]; then
        module_name=$(echo "$import_line" | sed 's/from\.import//')
        module_name=$(echo "$module_name" | xargs)
        if [ -d "$MODULE_PATH/$module_name" ] || [ -f "$MODULE_PATH/${module_name}.py" ]; then
            log_success "Import válido: $module_name"
        else
            log_error "Import inválido: $module_name (archivo/carpeta no existe)"
        fi
    fi
done

# Verificar imports en models/__init__.py
grep "import" $MODULE_PATH/models/__init__.py | while read -r import_line; do
    if [[ $import_line =~ from\.import(.+) ]]; then
        model_file=$(echo "$import_line" | sed 's/from\.import//')
        model_file=$(echo "$model_file" | xargs)
        if [ -f "$MODULE_PATH/models/${model_file}.py" ]; then
            log_success "Modelo importado: $model_file.py"
        else
            log_error "Modelo no encontrado: $model_file.py"
        fi
    fi
done

# 6. VERIFICACIÓN DE DEPENDENCIAS
echo "" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "6. VERIFICACIÓN DE DEPENDENCIAS" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE

# Extraer dependencias del manifest
DEPENDS=$(grep -A 20 "'depends'" $MODULE_PATH/__manifest__.py | grep -o "'[a-z_]*'" | tr -d "'")

for dep in $DEPENDS; do
    if [ "$dep" != "depends" ]; then
        log_success "Dependencia declarada: $dep"
        # Verificar si existe en Odoo base
        if [ -f "/usr/lib/python3/dist-packages/odoo/addons/${dep}/__manifest__.py" ]; then
            log_success "Dependencia base válida: $dep"
        else
            log_warning "Dependencia externa: $dep (asegúrate de que esté disponible)"
        fi
    fi
done

# 7. VERIFICACIÓN DE REFERENCIAS CRUZADAS
echo "" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "7. VERIFICACIÓN DE REFERENCIAS CRUZADAS" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE

# Buscar todos los Many2one, One2many, Many2many
grep -r "fields\.Many2one\|fields\.One2many\|fields\.Many2many" $MODULE_PATH/models/ | while read -r line; do
    file=$(echo "$line" | cut -d':' -f1)
    model_ref=$(echo "$line" | grep -o "comodel_name='[^']*'" | cut -d"'" -f2)
    if [ -z "$model_ref" ]; then
        model_ref=$(echo "$line" | grep -o "'[a-z_.]*'" | head -1 | tr -d "'")
    fi
    log_success "Referencia a modelo: $model_ref en $file"
done

# 8. VERIFICACIÓN DE XMLID
echo "" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "8. VERIFICACIÓN DE XMLIDS" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE

# Buscar todos los xmlid definidos
grep -r 'id="' $MODULE_PATH | grep -o 'id="[^"]*"' | cut -d'"' -f2 | sort -u | while read -r xmlid; do
    log_success "XMLID definido: $xmlid"
done

# 9. VERIFICACIÓN DE HERENCIA PYTHON
echo "" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "9. VERIFICACIÓN DE HERENCIA PYTHON" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE

for py_file in $(find $MODULE_PATH/models -name "*.py" -type f); do
    class_lines=$(grep -n "class.*models.Model" "$py_file")
    if [ -n "$class_lines" ]; then
        log_success "Clase Model encontrada en $py_file"
    fi
    
    # Verificar si usa models.Model sin importar
    if grep -q "models.Model" "$py_file" && ! grep -q "from odoo import.*models" "$py_file"; then
        log_error "Uso de models.Model sin importar models en $py_file"
    fi
done

# 10. RESUMEN FINAL
echo "" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE
echo "10. RESUMEN FINAL" >> $REPORT_FILE
echo "════════════════════════════════════════════════════════════════" >> $REPORT_FILE

echo "" | tee -a $REPORT_FILE
echo "📊 ESTADÍSTICAS:" | tee -a $REPORT_FILE
echo "   Errores encontrados: $ERRORS" | tee -a $REPORT_FILE
echo "   Warnings encontrados: $WARNINGS" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

if [ $ERRORS -eq 0 ]; then
    echo "🎉 ¡AUDITORÍA COMPLETADA SIN ERRORES CRÍTICOS!" | tee -a $REPORT_FILE
    exit 0
else
    echo "❌ SE ENCONTRARON ERRORES CRÍTICOS" | tee -a $REPORT_FILE
    echo "📄 Reporte completo guardado en: $REPORT_FILE" | tee -a $REPORT_FILE
    exit 1
fi
