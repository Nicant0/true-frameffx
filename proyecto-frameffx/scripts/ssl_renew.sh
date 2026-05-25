#!/bin/bash
# Script para renovar certificados SSL con Certbot

set -e

DOMAIN="yourdomain.com"
EMAIL="admin@yourdomain.com"

echo "================================"
echo "🔐 Renovando certificados SSL"
echo "================================"

# Cambiar a directorio del proyecto
cd "$(dirname "$0")/.."

echo "📋 Verificando certificados existentes..."
if [ -d "docker/certbot/conf/live/$DOMAIN" ]; then
    echo "♻️  Renovando certificado existente..."
    docker-compose -f docker/docker-compose.prod.yml run --rm certbot renew --webroot
else
    echo "🆕 Obteniendo nuevo certificado..."
    docker-compose -f docker/docker-compose.prod.yml run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d www.$DOMAIN
fi

echo "🔄 Recargando Nginx..."
docker-compose -f docker/docker-compose.prod.yml exec -T nginx nginx -s reload

echo "================================"
echo "✅ Certificados SSL actualizados"
echo "================================"
