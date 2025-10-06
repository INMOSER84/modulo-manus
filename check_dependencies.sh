#!/bin/bash
MANIFEST="$1"
if grep -qo 'account_accountant' "$MANIFEST"; then
    echo "¡Dependencia 'account_accountant' detectada! Incompatible con Community Edition."
fi
