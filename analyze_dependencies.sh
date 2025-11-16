#!/bin/bash
echo "=== ANÁLISIS DE DEPENDENCIAS OCA ==="
echo ""
echo "Módulos declarados en manifiestos:"
grep -h "depends" custom_addons/*/__manifest__.py | \
    grep -o "'[^']*'" | \
    sed "s/'//g" | \
    sort -u

echo ""
echo "Importaciones de módulos externos:"
grep -rh "from.*import" custom_addons --include="*.py" | \
    grep -v "^#" | \
    grep "fieldservice\|agreement\|contract" | \
    sort -u