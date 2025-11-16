#!/bin/bash

# Nombre de la base de datos
DB="odoo_mx"

# Lista de módulos base y dependencias
MODULES=(
  "base"
  "contacts"
  "product"
  "hr"
  "sale_management"
  "mail"
  "stock"
)

# Actualizar módulos base
echo "--------------------------------------------"
echo "  ACTUALIZANDO MÓDULOS BASE"
echo "--------------------------------------------"
for MODULE in "${MODULES[@]}"; do
    echo "Actualizando módulo: $MODULE"
    docker exec -it odoo_project-odoo-1 odoo -d $DB -u $MODULE --stop-after-init
done

# Actualizar módulo personalizado
echo "--------------------------------------------"
echo "  ACTUALIZANDO MÓDULO PERSONALIZADO: INMOSER_SERVICE_ORDER"
echo "--------------------------------------------"
docker exec -it odoo_project-odoo-1 odoo -d $DB -u inmoser_service_order --stop-after-init

echo "--------------------------------------------"
echo "  TODOS LOS MÓDULOS SE ACTUALIZARON CORRECTAMENTE"
echo "--------------------------------------------"
