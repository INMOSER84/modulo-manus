#!/bin/bash
# Nombre: restart_odoo.sh
# Descripción: Reinicia Odoo en Docker, libera puerto 8069 y ejecuta instalación de módulo inmoser_manus

MODULE_NAME="inmoser_manus"
DB_NAME="inmoser"

echo "🛑 Matando cualquier proceso en el puerto 8069..."
sudo fuser -k 8069/tcp

echo "⬇️ Bajando contenedores existentes..."
sudo docker-compose down

echo "⬆️ Levantando contenedores en segundo plano..."
sudo docker-compose up -d

echo "⏳ Esperando a que Odoo esté listo..."
# Espera hasta que Odoo responda en localhost:8069
until curl -s http://localhost:8069 > /dev/null; do
    echo -n "."
    sleep 2
done
echo -e "\n✅ Odoo está listo."

echo "⚙️ Instalando módulo ${MODULE_NAME} en la base ${DB_NAME}..."
sudo docker-compose exec odoo odoo -d $DB_NAME -i $MODULE_NAME --without-demo=all --stop-after-init

echo "🎉 Proceso completado."
