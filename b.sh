#!/bin/bash
# l10n_mx_robust_fix.sh - MANTENIMIENTO PROFESIONAL L10N_MX OPTIMIZADO

set -e  # Salir inmediatamente si hay error

# ==================== CONFIGURACIÓN ====================
readonly CUSTOM_ADDONS_PATH="/home/baruc/odoo_project/custom_addons"
readonly DB_NAME="odoo_mx"
readonly CONTAINER_NAME="odoo_project-odoo-1"
readonly DB_CONTAINER="odoo_project-db-1"
readonly PROJECT_PATH="/home/baruc/odoo_project"

# Módulos L10N (SEPARADOS POR ESPACIOS)
readonly L10N_MODULES="l10n_mx l10n_mx_edi l10n_mx_einvoicing"

# Array para warnings
declare -a WARNINGS=()

# ==================== FUNCIONES DE UTILIDAD ====================

print_header() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "  $1"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ ERROR: $1" >&2
}

log_warning() {
    echo "⚠️  WARNING: $1"
    WARNINGS+=("$1")
}

# ==================== VERIFICACIONES PREVIAS ====================

check_requirements() {
    print_header "🔍 VERIFICACIONES PREVIAS"
    
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script debe ejecutarse con sudo"
        echo "    Ejecuta: sudo $0"
        exit 1
    fi
    
    if [ ! -d "$PROJECT_PATH" ]; then
        log_error "Directorio de proyecto no encontrado: $PROJECT_PATH"
        exit 1
    fi
    
    if [ ! -f "$PROJECT_PATH/docker-compose.yml" ]; then
        log_error "docker-compose.yml no encontrado en $PROJECT_PATH"
        exit 1
    fi
    
    if ! command -v xmllint &> /dev/null; then
        log_warning "xmllint no instalado (opcional). Instala con: sudo apt install libxml2-utils"
    fi
    
    log_success "Verificaciones completadas"
}

# ==================== FASE 1: LIMPIEZA ====================

cleanup_cache() {
    print_header "🧹 LIMPIEZA DE CACHÉ"
    
    cd "$CUSTOM_ADDONS_PATH" || exit 1

    local cache_count=$(find . -type d -name "__pycache__" | wc -l)
    if [ "$cache_count" -gt 0 ]; then
        find . -type d -name "__pycache__" -exec rm -rf {} +
        log_success "Eliminados $cache_count directorios __pycache__"
    fi
    
    local pyc_count=$(find . -name "*.pyc" | wc -l)
    if [ "$pyc_count" -gt 0 ]; then
        find . -name "*.pyc" -delete
        log_success "Eliminados $pyc_count archivos .pyc"
    fi
}

# ==================== FASE 2: PERMISOS ====================

fix_permissions() {
    print_header "🔐 CORRIGIENDO PERMISOS"
    
    chown -R 101:101 "${CUSTOM_ADDONS_PATH}"
    log_success "Propietario cambiado a 101:101"

    find "${CUSTOM_ADDONS_PATH}" -type d -exec chmod 755 {} \;
    find "${CUSTOM_ADDONS_PATH}" -type f -exec chmod 644 {} \;

    local uid_gid=$(stat -c "%u:%g" "${CUSTOM_ADDONS_PATH}")
    log_success "Verificación de permisos OK: $uid_gid"
}

# ==================== FASE 3: DOCKER ====================

start_containers() {
    print_header "🐳 INICIANDO CONTENEDORES"
    
    cd "$PROJECT_PATH"
    docker compose up -d
    
    echo "⏳ Esperando contenedor Odoo..."
    sleep 20
}

# ==================== FASE 4: ESPERAR BD ====================

wait_for_database() {
    print_header "⏳ ESPERANDO BASE DE DATOS"
    
    local timeout=60
    while ! docker exec "$DB_CONTAINER" pg_isready -U odoo >/dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            log_error "Timeout esperando PostgreSQL"
            exit 1
        fi
    done
    
    log_success "PostgreSQL está listo"
}

# ==================== FASE 5: ACTUALIZAR MÓDULOS ====================

module_exists() {
    docker exec "$DB_CONTAINER" psql -U odoo -d "$DB_NAME" -t -c \
        "SELECT name FROM ir_module_module WHERE name='$1' AND state IN ('installed', 'to upgrade') LIMIT 1;" | xargs
}

update_l10n_modules() {
    print_header "📦 ACTUALIZANDO MÓDULOS L10N_MX (PASO ÚNICO)"

    echo "🔄 Actualizando lista base de módulos..."
    docker exec "$CONTAINER_NAME" /usr/bin/odoo update -d "$DB_NAME" -u base --stop-after-init
    log_success "Lista base actualizada"
    
    local modules_to_update=""
    
    for module in $L10N_MODULES; do
        if [ "$(module_exists $module)" == "$module" ]; then
            modules_to_update+="${module},"
        else
            log_warning "Módulo $module NO existe o no está instalado en la BD. Se omitirá."
        fi
    done

    if [ -n "$modules_to_update" ]; then
        modules_to_update=${modules_to_update%,}
        echo "➡️ Actualizando: $modules_to_update"
        
        docker exec "$CONTAINER_NAME" /usr/bin/odoo update -d "$DB_NAME" -u "$modules_to_update" --stop-after-init
        
        log_success "Actualización L10N_MX completada"
    else
        log_success "No hay módulos L10N_MX instalados para actualizar"
    fi
}

# ==================== FASE 6: VERIFICACIÓN ====================

verify_installation() {
    print_header "🔍 VERIFICACIÓN FINAL"

    docker exec "$DB_CONTAINER" psql -U odoo -d "$DB_NAME" -c \
        "SELECT name, state, latest_version FROM ir_module_module WHERE name LIKE 'l10n_mx%';"

    echo ""
    local errors=$(docker logs "$CONTAINER_NAME" --since 5m 2>&1 | grep -c "ERROR\|Traceback" || true)

    if [ "$errors" -gt 0 ]; then
        log_warning "Detectados $errors errores recientes en logs"
    else
        log_success "Sin errores recientes"
    fi
}

# ==================== MENÚ EMERGENCIA ====================

emergency_menu() {
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "🚨 MENÚ DE EMERGENCIA"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "1. Ver logs: docker logs $CONTAINER_NAME --tail=200"
    echo "2. Instalar módulo: docker exec $CONTAINER_NAME odoo install -d $DB_NAME -i MODULO"
    echo "3. Revisar BD: docker exec -it $DB_CONTAINER psql -U odoo -d $DB_NAME"
    echo ""
}

# ==================== MAIN ====================

main() {
    check_requirements
    cleanup_cache
    fix_permissions
    start_containers
    wait_for_database
    update_l10n_modules
    verify_installation

    if [ ${#WARNINGS[@]} -gt 0 ]; then
        emergency_menu
    fi

    print_header "✅ PROCESO COMPLETADO"
    echo "    → Abre Odoo: http://localhost:8069"
}

main "$@"
