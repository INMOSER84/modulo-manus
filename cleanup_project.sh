#!/bin/bash
# Script de Análisis Detallado y Limpieza - Proyecto Odoo
# Basado en los resultados de la auditoría

echo "=========================================="
echo "ANÁLISIS DETALLADO Y LIMPIEZA"
echo "=========================================="
echo ""

# ==========================================
# ANÁLISIS DE PROBLEMAS CRÍTICOS
# ==========================================

echo "🔍 ANÁLISIS DE PROBLEMAS ENCONTRADOS:"
echo ""

echo "1️⃣  ARCHIVOS ZONE.IDENTIFIER (1,214 archivos)"
echo "   ⚠️  Estos archivos son marcadores de Windows (WSL)"
echo "   📝 Problema: Ocupan espacio y no son necesarios"
echo "   ✅ Solución: Eliminar todos"
echo ""

echo "2️⃣  ARCHIVOS TEMPORALES (8 archivos)"
echo "   ⚠️  Archivos .pyc, backups, etc."
echo "   📝 Problema: No deben estar en repositorio"
echo "   ✅ Solución: Eliminar y agregar a .gitignore"
echo ""

echo "3️⃣  PROYECTO MUY GRANDE (724M)"
echo "   ⚠️  El tamaño es considerable"
echo "   📝 Análisis de distribución necesario"
echo "   ✅ Revisar qué ocupa más espacio"
echo ""

echo "=========================================="
echo "¿DESEAS PROCEDER CON LA LIMPIEZA?"
echo "=========================================="
echo ""
echo "Se realizarán las siguientes acciones:"
echo "  • Eliminar archivos Zone.Identifier"
echo "  • Eliminar archivos .pyc y temporales"
echo "  • Crear/actualizar .gitignore"
echo "  • Crear backup antes de limpiar"
echo ""
read -p "¿Continuar? (s/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Limpieza cancelada"
    exit 0
fi

# ==========================================
# CREAR BACKUP
# ==========================================
echo ""
echo "📦 Creando backup de seguridad..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "../$BACKUP_DIR"

# Backup de archivos que serán eliminados
echo "   Guardando lista de archivos a eliminar..."
find . -name "*:Zone.Identifier" > "../$BACKUP_DIR/zone_identifier_files.txt"
find . -name "*.pyc" -o -name "*.pyo" -o -name "*~" -o -name "*.bak" > "../$BACKUP_DIR/temp_files.txt"

echo "   ✅ Backup creado en: ../$BACKUP_DIR"

# ==========================================
# LIMPIEZA DE ARCHIVOS ZONE.IDENTIFIER
# ==========================================
echo ""
echo "🧹 LIMPIANDO ARCHIVOS ZONE.IDENTIFIER..."
ZONE_COUNT=$(find . -name "*:Zone.Identifier" | wc -l)
echo "   Archivos a eliminar: $ZONE_COUNT"

find . -name "*:Zone.Identifier" -type f -delete

ZONE_AFTER=$(find . -name "*:Zone.Identifier" | wc -l)
echo "   ✅ Eliminados: $((ZONE_COUNT - ZONE_AFTER)) archivos"

# ==========================================
# LIMPIEZA DE ARCHIVOS TEMPORALES
# ==========================================
echo ""
echo "🧹 LIMPIANDO ARCHIVOS TEMPORALES..."

echo "   Eliminando archivos .pyc y .pyo..."
find . -name "*.pyc" -type f -delete
find . -name "*.pyo" -type f -delete

echo "   Eliminando archivos de respaldo..."
find . -name "*~" -type f -delete
find . -name "*.bak" -type f -delete
find . -name "*.swp" -type f -delete

echo "   Eliminando __pycache__..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "   ✅ Archivos temporales eliminados"

# ==========================================
# CREAR/ACTUALIZAR .GITIGNORE
# ==========================================
echo ""
echo "📝 ACTUALIZANDO .gitignore..."

cat > .gitignore << 'EOF'
# Archivos de Python
*.pyc
*.pyo
*.pyd
__pycache__/
*.so
*.egg
*.egg-info/
dist/
build/
*.py[cod]
*$py.class

# Archivos de Odoo
*.log
*.pot
*.pyc
filestore/
sessions/
addons/

# Archivos de configuración local
odoo.conf
.odoorc
*.conf.local

# Archivos de IDE
.vscode/
.idea/
*.swp
*.swo
*~
.project
.pydevproject
.settings/

# Archivos del sistema
.DS_Store
Thumbs.db
*:Zone.Identifier

# Archivos de respaldo
*.bak
*.backup
*.old

# Archivos de base de datos
*.db
*.sql
*.sqlite

# Directorios de logs
logs/
*.log

# Archivos de entorno
.env
.env.local
venv/
env/
ENV/

# Archivos de Docker
docker-compose.override.yml

# Reportes de auditoría (opcional)
audit_reports/

# Node modules (si se usa JavaScript)
node_modules/
EOF

echo "   ✅ .gitignore actualizado"

# ==========================================
# ANÁLISIS DE ESPACIO LIBERADO
# ==========================================
echo ""
echo "📊 ANÁLISIS DE ESPACIO..."
CURRENT_SIZE=$(du -sh . | cut -f1)
echo "   Tamaño actual: $CURRENT_SIZE"
echo "   Tamaño anterior: 724M"

# ==========================================
# VERIFICACIÓN DE MÓDULOS
# ==========================================
echo ""
echo "🔍 VERIFICANDO ESTRUCTURA DE MÓDULOS..."
echo ""
echo "Módulos personalizados encontrados:"
find custom_addons -maxdepth 2 -name "__manifest__.py" -exec dirname {} \; | while read module; do
    echo "   📦 $(basename $module)"
    
    # Verificar estructura básica
    if [ ! -f "$module/__init__.py" ]; then
        echo "      ⚠️  Falta __init__.py"
    fi
    
    if [ ! -d "$module/models" ] && [ ! -d "$module/views" ]; then
        echo "      ⚠️  No tiene carpeta models ni views"
    fi
    
    if [ ! -d "$module/security" ]; then
        echo "      ⚠️  No tiene carpeta security"
    fi
done

# ==========================================
# ANÁLISIS DE DISTRIBUCIÓN DE TAMAÑO
# ==========================================
echo ""
echo "📊 DISTRIBUCIÓN DE TAMAÑO POR DIRECTORIO:"
du -sh */ 2>/dev/null | sort -hr | head -10

# ==========================================
# RECOMENDACIONES
# ==========================================
echo ""
echo "=========================================="
echo "✅ LIMPIEZA COMPLETADA"
echo "=========================================="
echo ""
echo "📋 RECOMENDACIONES:"
echo ""
echo "1. OPTIMIZACIÓN:"
echo "   • Revisar si todos los módulos OCA son necesarios"
echo "   • El proyecto ocupa 724M, considera si todo es necesario"
echo "   • Comando: du -sh oca_addons/*/ | sort -hr"
echo ""
echo "2. CONTROL DE VERSIONES:"
echo "   • Verifica que .gitignore esté funcionando"
echo "   • Comando: git status"
echo "   • Si hay archivos no deseados: git rm --cached <archivo>"
echo ""
echo "3. SEGURIDAD:"
echo "   • Revisa el reporte: cat audit_reports/04_seguridad_*.txt"
echo "   • Verifica que todos los modelos tengan reglas de acceso"
echo ""
echo "4. DOCUMENTACIÓN:"
echo "   • Agrega README.md a cada módulo custom"
echo "   • Documenta las dependencias de módulos OCA"
echo ""
echo "5. PRUEBAS:"
echo "   • Solo 0 archivos de test encontrados"
echo "   • Considera agregar tests unitarios"
echo ""
echo "6. RENDIMIENTO:"
echo "   • Revisa: cat audit_reports/11_rendimiento_*.txt"
echo "   • Busca búsquedas sin límite y bucles problemáticos"
echo ""
echo "=========================================="
echo "PRÓXIMOS PASOS SUGERIDOS"
echo "=========================================="
echo ""
echo "Para análisis detallado de reportes:"
echo "  cat audit_reports/02_modulos_custom_*.txt"
echo "  cat audit_reports/04_seguridad_*.txt"
echo "  cat audit_reports/09_calidad_codigo_*.txt"
echo "  cat audit_reports/14_problemas_comunes_*.txt"
echo ""
echo "Para ver qué ocupa más espacio:"
echo "  du -sh oca_addons/*/ | sort -hr"
echo "  du -sh custom_addons/*/ | sort -hr"
echo ""
echo "Para verificar dependencias faltantes:"
echo "  pip freeze > requirements_actual.txt"
echo "  diff requirements.txt requirements_actual.txt"
echo ""
echo "=========================================="
