#!/bin/bash
# Script para inicializar la base de datos en producción

set -e

echo "================================"
echo "📊 Inicializando base de datos"
echo "================================"

# Cambiar a directorio del proyecto
cd "$(dirname "$0")/.."

echo "⏳ Esperando a PostgreSQL..."
docker-compose -f docker/docker-compose.prod.yml exec -T postgres pg_isready -U $DB_USER

echo "✅ PostgreSQL está listo"

echo "🔄 Ejecutando migraciones..."
docker-compose -f docker/docker-compose.prod.yml exec -T web python manage.py migrate

echo "📁 Recopilando estáticos..."
docker-compose -f docker/docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo "👤 Creando superusuario..."
docker-compose -f docker/docker-compose.prod.yml exec -T web python manage.py createsuperuser

echo "================================"
echo "✨ Base de datos inicializada"
echo "================================"
