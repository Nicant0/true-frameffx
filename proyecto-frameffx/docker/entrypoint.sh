#!/bin/bash
# Entrypoint script para inicializar la aplicación Django

set -e

echo "================================"
echo "🚀 Iniciando aplicación Django"
echo "================================"

# Wait for database
echo "⏳ Esperando a PostgreSQL..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL está listo"

# Run migrations with proper dependency order
echo "📊 Ejecutando migraciones..."
# First, migrate the users app (dependency for other apps)
echo "  → Migrando aplicación 'users'..."
python manage.py migrate users --noinput
# Then migrate all remaining apps
echo "  → Migrando todas las aplicaciones..."
python manage.py migrate --noinput
echo "✅ Migraciones completadas"

# Collect static files
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput
echo "✅ Archivos estáticos recopilados"

# Create superuser if it doesn't exist
echo "👤 Verificando superusuario..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin@example.com', 'changeme')
    print("✅ Superusuario creado: admin@example.com / changeme")
else:
    print("✅ Superusuario ya existe")
END

echo "================================"
echo "✨ Aplicación lista"
echo "================================"

# Start Gunicorn
exec gunicorn FrameffX.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --access-logfile - \
    --error-logfile -
