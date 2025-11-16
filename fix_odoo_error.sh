#!/bin/bash

# Script para corregir el error "duplicate key value violates unique constraint stock_warehouse_warehouse_code_uniq" en Odoo.
# Este error ocurre al intentar instalar el módulo 'stock' cuando ya existe un almacén con el código 'WH'.

DB_NAME="odoo_mx"

echo "Iniciando la corrección de errores para la base de datos: $DB_NAME"

# 1. Eliminar el registro duplicado de ir.model.data que causa el error.
# Esto se hace para permitir que Odoo cargue el archivo XML sin intentar crear un registro duplicado.
echo "Paso 1: Eliminando el registro 'warehouse0' de ir.model.data si existe..."
psql -d $DB_NAME -c "DELETE FROM ir_model_data WHERE module = 'stock' AND name = 'warehouse0';"

# 2. Eliminar el almacén 'WH' existente para permitir que Odoo lo recree correctamente.
# Opcional: Si el almacén existente es el que se desea mantener, se podría renombrar.
# Sin embargo, para una instalación limpia del módulo, es mejor eliminarlo si no tiene movimientos.
echo "Paso 2: Eliminando el almacén con código 'WH' si existe..."
psql -d $DB_NAME -c "DELETE FROM stock_warehouse WHERE code = 'WH';"

# 3. Reintentar la instalación del módulo 'stock'.
echo "Paso 3: Reinstalando el módulo 'stock'..."
# Se asume que el comando original se ejecutó desde el directorio de Odoo o que 'odoo' está en el PATH.
# Se utiliza '-u' (update) en lugar de '-i' (install) para forzar la actualización de los datos del módulo.
odoo -d $DB_NAME -u stock --stop-after-init

echo "Proceso de corrección finalizado. Revise la salida del comando Odoo para confirmar el éxito."
