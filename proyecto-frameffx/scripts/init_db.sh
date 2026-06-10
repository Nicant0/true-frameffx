#!/bin/bash
# ============================================================
# init_db.sh — Inicializa la base de datos en producción
# Solo necesario si el entrypoint.sh no se ejecutó correctamente
# En condiciones normales el entrypoint.sh lo hace automáticamente
# ============================================================

set -e

# Cambiar a directorio del proyecto
cd "$(dirname "$0")/.."

echo "================================"
echo "📊 Inicializando base de datos"
echo "================================"

echo "⏳ Esperando a PostgreSQL..."
docker compose -f docker/docker-compose.prod.yml exec -T postgres pg_isready -U "${DB_USER:-frameffx_user}"

echo "✅ PostgreSQL está listo"

echo "🔄 Ejecutando migraciones..."
docker compose -f docker/docker-compose.prod.yml exec -T web python manage.py migrate

echo "📁 Recopilando estáticos..."
docker compose -f docker/docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo "👤 Creando superusuario (sigue las instrucciones)..."
docker compose -f docker/docker-compose.prod.yml exec web python manage.py createsuperuser

echo "================================"
echo "✨ Base de datos inicializada"
echo "================================"
