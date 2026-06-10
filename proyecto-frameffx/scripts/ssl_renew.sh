#!/bin/bash
# ============================================================
# ssl_renew.sh — Renueva el certificado SSL de Let's Encrypt
# Llamar manualmente o via cron cada ~2 meses
# ============================================================

set -e

# ── Directorio raíz del proyecto ───────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# ── Leer el dominio desde .env.prod ────────────────────────
if [ -f ".env.prod" ]; then
    DOMAIN=$(grep "^ALLOWED_HOSTS=" .env.prod | head -1 | cut -d'=' -f2 | cut -d',' -f1)
else
    echo "❌  No se encontró .env.prod. Ejecuta setup_prod.sh primero."
    exit 1
fi

if [ -z "$DOMAIN" ]; then
    echo "❌  No se pudo leer el dominio de .env.prod"
    exit 1
fi

echo "================================"
echo "🔐 Renovando certificado SSL"
echo "   Dominio: $DOMAIN"
echo "================================"

echo "📋 Verificando certificados existentes..."
if [ -d "docker/certbot/conf/live/$DOMAIN" ]; then
    echo "♻️  Renovando certificado existente..."
    docker run --rm \
        -v "$(pwd)/docker/certbot/conf:/etc/letsencrypt" \
        -v "$(pwd)/docker/certbot/www:/var/www/certbot" \
        certbot/certbot renew \
        --webroot \
        --webroot-path=/var/www/certbot \
        --non-interactive \
        --quiet
else
    echo "❌  No se encontró certificado para $DOMAIN"
    echo "   Ejecuta setup_prod.sh para obtener el certificado por primera vez."
    exit 1
fi

echo "🔄 Recargando Nginx..."
docker compose -f docker/docker-compose.prod.yml exec -T nginx nginx -s reload

echo "================================"
echo "✅ Certificado SSL actualizado"
echo "================================"
