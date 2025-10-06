#!/bin/bash
MODULE_PATH="$1"
REQUIRED_FILES=("__manifest__.py" "__init__.py")
REQUIRED_DIRS=("models" "views" "security")
MISSING=()

cd "$MODULE_PATH" || exit 1
for file in "${REQUIRED_FILES[@]}"; do
    [ ! -f "$file" ] && MISSING+=("$file")
done
for dir in "${REQUIRED_DIRS[@]}"; do
    [ ! -d "$dir" ] && MISSING+=("$dir")
done

if [ "${#MISSING[@]}" -eq 0 ]; then
    echo "Estructura mínima: OK"
else
    echo "FALTAN elementos: ${MISSING[*]}"
fi
