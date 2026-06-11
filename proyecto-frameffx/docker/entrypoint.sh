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
import os
User = get_user_model()
email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@frameffx.local')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
if not email or not password:
    print("⚠️  DJANGO_SUPERUSER_EMAIL o DJANGO_SUPERUSER_PASSWORD no definidos — se omite creación.")
elif not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email, password)
    print(f"✅ Superusuario creado: {email}")
else:
    print(f"✅ Superusuario ya existe: {email}")
END

echo "================================"
echo "✨ Aplicación lista"
echo "================================"

# Start Gunicorn
exec gunicorn FrameffX.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
