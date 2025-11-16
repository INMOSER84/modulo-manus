#!/bin/bash

# --- Script de Despliegue de Proyecto Odoo con Docker Compose ---

# 1. Detener y eliminar contenedores antiguos
echo "🔌 Deteniendo contenedores Odoo y PostgreSQL..."
docker-compose down

# 2. Reconstruir imágenes
echo "🔨 Reconstruyendo imágenes y asegurando que se lean los cambios en el código..."
docker-compose build --no-cache

# 3. Levantar los servicios en modo demonio
echo "✅ Iniciando servicios en segundo plano (Postgres y Odoo)..."
docker-compose up -d

# 4. Verificar estado
echo "👀 Estado actual de los contenedores:"
docker-compose ps

echo -e "\n--- Despliegue finalizado ---"
echo "URL de acceso: http://localhost:8069"
