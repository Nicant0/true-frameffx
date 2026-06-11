#!/bin/bash
# ============================================================
# setup_prod.sh — Configuración inicial de producción
# Ejecutar UNA VEZ en el servidor antes del primer despliegue
# ============================================================
#
# Uso:  bash scripts/setup_prod.sh
#
# Este script:
#   1. Pide interactivamente los datos de configuración
#   2. Genera el archivo .env.prod automáticamente
#   3. Actualiza el dominio en nginx/django.conf
#   4. Obtiene el certificado SSL (ACME challenge)
#   5. Activa HTTPS en nginx
#   6. Lanza los contenedores en producción
#
# ============================================================

set -e

# ── Colores ────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${GREEN}✅  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️   $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️   $1${NC}"; }
err()  { echo -e "${RED}❌  $1${NC}"; exit 1; }
ask()  { echo -e "${CYAN}${BOLD}?   $1${NC}"; }

# ── Directorio raíz del proyecto ───────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo ""
echo -e "${BOLD}============================================================${NC}"
echo -e "${BOLD}   FrameffX — Configuración de Producción${NC}"
echo -e "${BOLD}============================================================${NC}"
echo ""

# ── 1. Recoger datos de configuración ─────────────────────
info "Introduce los datos de configuración. Pulsa ENTER para usar el valor por defecto."
echo ""

ask "Dominio principal (ej: frameffx.online):"
read -r DOMAIN
[ -z "$DOMAIN" ] && err "El dominio es obligatorio."

ask "¿El dominio tiene www? (s/n) [s]:"
read -r HAS_WWW
HAS_WWW="${HAS_WWW:-s}"

ask "Email para Let's Encrypt (para certificado SSL):"
read -r LETSENCRYPT_EMAIL
[ -z "$LETSENCRYPT_EMAIL" ] && err "El email es obligatorio para el certificado SSL."

ask "Contraseña para la base de datos PostgreSQL [genera una aleatoria]:"
read -r DB_PASSWORD
if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)
    info "Contraseña generada automáticamente: $DB_PASSWORD"
fi

ask "Email del servidor de correo (Gmail recomendado, dejar vacío para consola):"
read -r EMAIL_HOST_USER

ask "Contraseña de aplicación del email (dejar vacío si no usas email real):"
read -r EMAIL_HOST_PASSWORD

ask "STRIPE_PUBLIC_KEY (dejar vacío para modo test placeholder):"
read -r STRIPE_PUBLIC_KEY
STRIPE_PUBLIC_KEY="${STRIPE_PUBLIC_KEY:-pk_test_placeholder}"

ask "STRIPE_SECRET_KEY (dejar vacío para modo test placeholder):"
read -r STRIPE_SECRET_KEY
STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY:-sk_test_placeholder}"

ask "STRIPE_WEBHOOK_SECRET (dejar vacío para placeholder):"
read -r STRIPE_WEBHOOK_SECRET
STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET:-whsec_placeholder}"

ask "Email del superusuario administrador (admin del panel Django):"
read -r DJANGO_SUPERUSER_EMAIL
DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-admin@${DOMAIN}}"

ask "Contraseña del superusuario administrador [genera una aleatoria]:"
read -r -s DJANGO_SUPERUSER_PASSWORD
if [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
    DJANGO_SUPERUSER_PASSWORD=$(openssl rand -base64 18 | tr -dc 'a-zA-Z0-9' | head -c 24)
    info "Contraseña de admin generada automáticamente: $DJANGO_SUPERUSER_PASSWORD"
else
    echo ""
fi

# ── 2. Calcular variables derivadas ────────────────────────
SECRET_KEY=$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#\$%^&*-_=+') for _ in range(50)))")

if [ "$HAS_WWW" = "s" ]; then
    ALLOWED_HOSTS="${DOMAIN},www.${DOMAIN}"
    SERVER_NAMES="${DOMAIN} www.${DOMAIN}"
    CERTBOT_DOMAINS="-d ${DOMAIN} -d www.${DOMAIN}"
else
    ALLOWED_HOSTS="${DOMAIN}"
    SERVER_NAMES="${DOMAIN}"
    CERTBOT_DOMAINS="-d ${DOMAIN}"
fi

EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
if [ -z "$EMAIL_HOST_USER" ]; then
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"
    warn "No se configuró email real → se usará el backend de consola."
fi

# ── 3. Generar .env.prod ───────────────────────────────────
ENV_FILE="$PROJECT_DIR/.env.prod"
info "Generando $ENV_FILE..."

cat > "$ENV_FILE" <<EOF
# ── Generado automáticamente por setup_prod.sh ──────────────
# NO versionar este archivo

# Django
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${ALLOWED_HOSTS}

# Base de datos PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=frameffx_db
DB_USER=frameffx_user
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=postgres
DB_PORT=5432

# Seguridad HTTPS (se activan una vez que SSL está disponible)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True

# Email
EMAIL_BACKEND=${EMAIL_BACKEND}
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=${EMAIL_HOST_USER}
EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}

# Stripe
STRIPE_PUBLIC_KEY=${STRIPE_PUBLIC_KEY}
STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}

# Superusuario inicial del panel de administración
# ¡Cambia la contraseña desde el admin tras el primer despliegue!
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD}
EOF

log ".env.prod generado correctamente"

# ── 4. Actualizar nginx/django.conf con el dominio ─────────
NGINX_CONF="$PROJECT_DIR/docker/nginx/django.conf"
info "Actualizando nginx con el dominio: $SERVER_NAMES"

# Reemplazar server_name en el bloque HTTP
sed -i "s/server_name _;/server_name ${SERVER_NAMES};/" "$NGINX_CONF"

log "Nginx configurado para: $SERVER_NAMES"

# ── 5. Crear directorios necesarios ───────────────────────
mkdir -p docker/certbot/conf docker/certbot/www
chmod +x scripts/*.sh docker/entrypoint.sh 2>/dev/null || true
log "Directorios y permisos configurados"

# ── 6. Levantar nginx solo en modo HTTP para el ACME Challenge ──
info "Levantando nginx en HTTP para el ACME Challenge..."
docker compose -f docker/docker-compose.prod.yml up -d nginx
sleep 3

# ── 7. Obtener certificado SSL ─────────────────────────────
info "Obteniendo certificado SSL de Let's Encrypt..."

docker run --rm \
    -v "$(pwd)/docker/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/docker/certbot/www:/var/www/certbot" \
    certbot/certbot certonly --webroot \
    -w /var/www/certbot \
    $CERTBOT_DOMAINS \
    --email "$LETSENCRYPT_EMAIL" \
    --agree-tos \
    --non-interactive \
    || err "Falló la obtención del certificado. Asegúrate de que el dominio apunta a este servidor y el puerto 80 está abierto."

log "Certificado SSL obtenido correctamente"

# ── 8. Activar bloque HTTPS en nginx/django.conf ──────────
info "Activando configuración HTTPS en nginx..."

# Descomentar el bloque HTTPS y configurar el dominio real
python3 - <<PYEOF
import re

with open("$NGINX_CONF", "r") as f:
    content = f.read()

# Descomentar el bloque HTTPS completo (quitar los '# ' del inicio de cada línea)
https_block_start = content.find("# ── Bloque HTTPS")
if https_block_start != -1:
    before = content[:https_block_start]
    after_raw = content[https_block_start:]
    # Quitar '# ' de cada línea del bloque HTTPS
    lines = after_raw.split('\n')
    uncommented = []
    for line in lines:
        if line.startswith('# '):
            uncommented.append(line[2:])
        elif line == '#':
            uncommented.append('')
        else:
            uncommented.append(line)
    content = before + '\n'.join(uncommented)

# Reemplazar el dominio placeholder en el bloque HTTPS
content = content.replace(
    "server_name frameffx.online www.frameffx.online;",
    "server_name ${SERVER_NAMES};"
)
content = content.replace(
    "/etc/letsencrypt/live/frameffx.online/fullchain.pem",
    "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
)
content = content.replace(
    "/etc/letsencrypt/live/frameffx.online/privkey.pem",
    "/etc/letsencrypt/live/${DOMAIN}/privkey.pem"
)

# Añadir redirección 301 de HTTP → HTTPS en el bloque HTTP
# Reemplazar todos los locations excepto acme-challenge en el bloque HTTP
# Primero encontramos el final de acme-challenge
acme_end = content.find("}", content.find("location /.well-known/acme-challenge/")) + 1

# Encontramos el final del bloque server HTTP (primer "}") que cierra el server
http_server_end = content.find("}", acme_end)
while True:
    # Verificamos si este } cierra el server o un location
    # En django.conf, despues del ultimo location hay un }
    next_bracket = content.find("}", http_server_end + 1)
    if next_bracket == -1 or "server {" in content[http_server_end:next_bracket]:
        break
    http_server_end = next_bracket

# Construimos el nuevo bloque HTTP
http_block_new = content[:acme_end] + "\n\n    # Redirigir todo el tráfico HTTP a HTTPS\n    location / {\n        return 301 https://\$host\$request_uri;\n    }\n" + content[http_server_end:]

content = http_block_new

with open("$NGINX_CONF", "w") as f:
    f.write(content)

print("OK")
PYEOF

log "Configuración HTTPS activada en nginx"

# ── 9. Levantar todos los servicios ───────────────────────
info "Levantando todos los contenedores..."
docker compose -f docker/docker-compose.prod.yml up -d --build

sleep 15

log "Contenedores en marcha"

# ── 10. Resumen final ──────────────────────────────────────
echo ""
echo -e "${BOLD}============================================================${NC}"
echo -e "${GREEN}${BOLD}   ✅  Despliegue completado${NC}"
echo -e "${BOLD}============================================================${NC}"
echo ""
echo -e "  🌐  Sitio web:    ${BOLD}https://${DOMAIN}${NC}"
echo -e "  🔑  Admin:        ${BOLD}https://${DOMAIN}/admin/${NC}"
echo -e "  💻  Admin email:  ${BOLD}${DJANGO_SUPERUSER_EMAIL}${NC}"
echo -e "  📊  DB Password:  ${BOLD}${DB_PASSWORD}${NC}  ← guárdala!"
echo -e "  📊  Admin Pass:   ${BOLD}${DJANGO_SUPERUSER_PASSWORD}${NC}  ← guárdala!"
echo ""
echo -e "  Para ver los logs:"
echo -e "  ${CYAN}docker compose -f docker/docker-compose.prod.yml logs -f${NC}"
echo ""
warn "¡Cambia la contraseña del superusuario desde el panel de administración!"
echo ""
