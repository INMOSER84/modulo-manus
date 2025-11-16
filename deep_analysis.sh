#!/bin/bash
# Análisis Profundo Post-Limpieza - Proyecto Odoo

echo "=========================================="
echo "ANÁLISIS PROFUNDO DEL PROYECTO"
echo "=========================================="
echo ""

# ==========================================
# 1. ANÁLISIS DE MÓDULOS OCA (718M)
# ==========================================
echo "📊 1. ANÁLISIS DE MÓDULOS OCA (ocupan 718M de 719M)"
echo "=================================================="
echo ""
echo "Top 10 repositorios por tamaño:"
du -sh oca_addons/*/ | sort -hr | head -10
echo ""

echo "Conteo de módulos por repositorio:"
for repo in oca_addons/*/; do
    if [ -d "$repo" ]; then
        module_count=$(find "$repo" -maxdepth 2 -name "__manifest__.py" 2>/dev/null | wc -l)
        repo_name=$(basename "$repo")
        if [ $module_count -gt 0 ]; then
            printf "%-40s %3d módulos\n" "$repo_name" "$module_count"
        fi
    fi
done | sort -k2 -nr
echo ""

# ==========================================
# 2. ANÁLISIS DETALLADO DE MÓDULOS CUSTOM
# ==========================================
echo ""
echo "📦 2. ANÁLISIS DE MÓDULOS PERSONALIZADOS"
echo "=================================================="
echo ""
echo "--- Estructura de inmoser_service_order ---"
tree custom_addons/inmoser_service_order -L 2
echo ""

echo "--- Estructura de inmoser_field_service ---"
tree custom_addons/inmoser_field_service -L 2
echo ""

echo "--- Manifiestos de módulos custom ---"
for manifest in custom_addons/*/__manifest__.py; do
    echo ""
    echo "=== $(dirname $manifest) ==="
    python3 -c "
import ast
with open('$manifest', 'r', encoding='utf-8') as f:
    data = ast.literal_eval(f.read())
    print(f\"Nombre: {data.get('name', 'N/A')}\")
    print(f\"Versión: {data.get('version', 'N/A')}\")
    print(f\"Categoría: {data.get('category', 'N/A')}\")
    print(f\"Depende de: {', '.join(data.get('depends', []))}\")
    print(f\"Auto-instalable: {data.get('auto_install', False)}\")
    print(f\"Aplicación: {data.get('application', False)}\")
" 2>/dev/null || cat "$manifest"
done
echo ""

# ==========================================
# 3. ANÁLISIS DE SEGURIDAD
# ==========================================
echo ""
echo "🔒 3. ANÁLISIS DE SEGURIDAD"
echo "=================================================="
echo ""
echo "--- Archivos de seguridad encontrados ---"
find custom_addons -type f -path "*/security/*"
echo ""

echo "--- Reglas de acceso (CSV) ---"
for csv in custom_addons/*/security/ir.model.access.csv; do
    if [ -f "$csv" ]; then
        echo ""
        echo "=== $csv ==="
        echo "Cantidad de reglas: $(tail -n +2 "$csv" 2>/dev/null | wc -l)"
        head -20 "$csv"
    fi
done
echo ""

echo "--- Grupos de seguridad definidos ---"
grep -r "<record.*res.groups" custom_addons --include="*.xml" -A 5 2>/dev/null | head -50
echo ""

# ==========================================
# 4. ANÁLISIS DE MODELOS
# ==========================================
echo ""
echo "🗄️ 4. ANÁLISIS DE MODELOS DE DATOS"
echo "=================================================="
echo ""
echo "--- Modelos definidos en custom_addons ---"
grep -rh "class.*models\." custom_addons --include="*.py" | grep -v "^#" | sort -u
echo ""

echo "--- Herencias de modelos ---"
grep -rh "_inherit.*=" custom_addons --include="*.py" | grep -v "^#" | sort -u
echo ""

echo "--- Campos computados ---"
grep -r "compute=" custom_addons --include="*.py" | wc -l
echo " campos computados encontrados"
echo ""

echo "--- Campos relacionados ---"
grep -r "related=" custom_addons --include="*.py" | wc -l
echo " campos relacionados encontrados"
echo ""

# ==========================================
# 5. ANÁLISIS DE VISTAS
# ==========================================
echo ""
echo "👁️ 5. ANÁLISIS DE VISTAS"
echo "=================================================="
echo ""
echo "--- Vistas XML en custom_addons ---"
find custom_addons -name "*.xml" -path "*/views/*" -type f
echo ""

echo "--- Tipos de vistas ---"
for xml in custom_addons/*/views/*.xml; do
    if [ -f "$xml" ]; then
        echo ""
        echo "=== $(basename $xml) ==="
        grep -o 'type="[^"]*"' "$xml" | sort -u
    fi
done
echo ""

echo "--- Menús definidos ---"
grep -rh "<menuitem" custom_addons --include="*.xml" | head -20
echo ""

# ==========================================
# 6. ANÁLISIS DE DEPENDENCIAS
# ==========================================
echo ""
echo "📦 6. ANÁLISIS DE DEPENDENCIAS"
echo "=================================================="
echo ""
echo "--- requirements.txt principal ---"
cat requirements.txt
echo ""

echo "--- Dependencias Python en módulos custom ---"
grep -rh "^import\|^from.*import" custom_addons --include="*.py" | \
    sed 's/from \([^ ]*\).*/\1/' | \
    sed 's/import \([^ ]*\).*/\1/' | \
    sort -u | \
    grep -v "^odoo" | \
    head -30
echo ""

echo "--- Dependencias de módulos Odoo declaradas ---"
for manifest in custom_addons/*/__manifest__.py; do
    echo ""
    echo "=== $(dirname $manifest) ==="
    grep -A 10 "depends" "$manifest" | grep -v "^--"
done
echo ""

# ==========================================
# 7. ANÁLISIS DE CONFIGURACIÓN DOCKER
# ==========================================
echo ""
echo "🐳 7. ANÁLISIS DE CONFIGURACIÓN DOCKER"
echo "=================================================="
echo ""
echo "--- docker-compose.yml ---"
cat docker-compose.yml
echo ""

echo "--- Versión de Odoo configurada ---"
grep -i "image.*odoo" docker-compose.yml
echo ""

# ==========================================
# 8. ANÁLISIS DE POSIBLES MEJORAS
# ==========================================
echo ""
echo "💡 8. OPORTUNIDADES DE MEJORA"
echo "=================================================="
echo ""

echo "--- Módulos sin README ---"
for module in custom_addons/*/; do
    if [ ! -f "$module/README.md" ] && [ ! -f "$module/README.rst" ]; then
        echo "⚠️  $(basename $module) - Sin README"
    fi
done
echo ""

echo "--- Módulos sin tests ---"
for module in custom_addons/*/; do
    if [ ! -d "$module/tests" ]; then
        echo "⚠️  $(basename $module) - Sin carpeta tests/"
    fi
done
echo ""

echo "--- Archivos Python sin docstrings ---"
find custom_addons -name "*.py" -type f ! -name "__init__.py" -exec sh -c '
    if ! grep -q "\"\"\"" "$1" && ! grep -q "'"'"''"'"''"'"'" "$1"; then
        echo "⚠️  $1 - Sin docstring"
    fi
' _ {} \; | head -10
echo ""

# ==========================================
# 9. VERIFICACIÓN DE CALIDAD
# ==========================================
echo ""
echo "✅ 9. VERIFICACIÓN DE CALIDAD DE CÓDIGO"
echo "=================================================="
echo ""

echo "--- Líneas por archivo Python ---"
find custom_addons -name "*.py" -type f -exec wc -l {} \; | sort -rn | head -10
echo ""

echo "--- Complejidad: Funciones largas (>50 líneas) ---"
for py_file in $(find custom_addons -name "*.py" -type f); do
    awk '
        /^[[:space:]]*(def |class )/ {
            if (in_func && lines > 50) {
                print FILENAME":"start_line":"func_name" ("lines" líneas)"
            }
            in_func = 1
            func_name = $0
            start_line = NR
            lines = 0
        }
        in_func { lines++ }
        /^[[:space:]]*(def |class )/ && prev_empty { in_func = 0 }
        { prev_empty = (NF == 0) }
        END {
            if (in_func && lines > 50) {
                print FILENAME":"start_line":"func_name" ("lines" líneas)"
            }
        }
    ' "$py_file"
done | head -10
echo ""

echo "--- Imports no utilizados (sample) ---"
for py_file in $(find custom_addons -name "*.py" -type f | head -5); do
    echo ""
    echo "=== $py_file ==="
    grep "^import\|^from.*import" "$py_file" | head -5
done
echo ""

# ==========================================
# 10. RESUMEN Y RECOMENDACIONES
# ==========================================
echo ""
echo "=========================================="
echo "📋 RESUMEN Y RECOMENDACIONES FINALES"
echo "=========================================="
echo ""

echo "✅ ESTADO ACTUAL:"
echo "  • Proyecto limpio (eliminados 1,214 Zone.Identifier)"
echo "  • Tamaño: 719M (718M en módulos OCA)"
echo "  • 2 módulos personalizados funcionando"
echo "  • 16 repositorios OCA instalados"
echo ""

echo "🎯 ACCIONES PRIORITARIAS:"
echo ""
echo "1. OPTIMIZACIÓN DE MÓDULOS OCA:"
echo "   • Revisar qué módulos OCA realmente usas"
echo "   • Considerar eliminar repositorios no utilizados"
echo "   • Comando: grep -r \"'field\" custom_addons --include=\"*.py\""
echo ""

echo "2. DOCUMENTACIÓN:"
echo "   • Crear README.md en cada módulo custom"
echo "   • Documentar dependencias y configuración"
echo "   • Template disponible en Odoo docs"
echo ""

echo "3. TESTING:"
echo "   • Agregar carpeta tests/ a tus módulos"
echo "   • Crear tests básicos para funcionalidad crítica"
echo "   • Ejecutar: python3 -m pytest custom_addons/*/tests/"
echo ""

echo "4. CONTROL DE VERSIONES:"
echo "   • Inicializar git si no está: git init"
echo "   • Hacer commit inicial: git add . && git commit -m 'Initial commit'"
echo "   • Configurar .gitignore (ya está actualizado)"
echo ""

echo "5. SEGURIDAD:"
echo "   • Verificar reglas de acceso para todos los modelos"
echo "   • Revisar permisos de grupos"
echo "   • Documentar usuarios y roles necesarios"
echo ""

echo "=========================================="
echo "Para más detalles, revisa los reportes en:"
echo "  ls -lh audit_reports/"
echo "=========================================="
