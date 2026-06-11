# FrameffX — Deployment Guide

Guía completa para desplegar FrameffX en un VPS con dominio.

> **Nota**: Para un primer despliegue totalmente automatizado usa el script
> `bash scripts/setup_prod.sh` que configura todo sin editar archivos manualmente.
> Esta guía es la referencia técnica detallada de cada paso.

---

## 📋 Requisitos

- VPS con Ubuntu 20.04+ o similar
- Docker Engine (v24+) y Docker Compose plugin v2 instalados
- Git instalado
- Dominio apuntando al VPS (DNS propagado)
- Acceso SSH al servidor
- Puertos 80 y 443 abiertos en el firewall

---

## 🚀 Instalación Inicial

### 1. Conectarse al VPS

```bash
ssh usuario@IP_DEL_VPS
```

### 2. Instalar dependencias

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker Engine (incluye el plugin Compose v2)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker    # aplica el grupo sin cerrar sesión

# Verificar instalación
docker --version
docker compose version

# Instalar Git
sudo apt install -y git
```

> **Importante**: Usar `docker compose` (v2, plugin integrado), NO `docker-compose` (v1, obsoleto y descontinuado).

### 3. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/frameffx.git
cd frameffx/proyecto-frameffx
```

### 4. Despliegue automatizado (recomendado)

```bash
chmod +x scripts/setup_prod.sh
bash scripts/setup_prod.sh
```

El script pedirá de forma interactiva: dominio, email SSL, contraseñas de BD, credenciales de Stripe y el **email/contraseña del superusuario administrador** (los genera aleatoriamente si se pulsa ENTER). Genera `.env.prod`, configura nginx, obtiene SSL y levanta los contenedores. Al terminar muestra un resumen con todas las credenciales.

---

## ⚙️ Configuración manual (referencia)

Si prefieres hacerlo paso a paso:

### Crear .env.prod

```bash
cp .env.example .env.prod
nano .env.prod
```

**Variables obligatorias:**

```env
# Django
SECRET_KEY=<cadena-aleatoria-50-caracteres>
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=frameffx_db
DB_USER=frameffx_user
DB_PASSWORD=<contraseña-segura>
DB_HOST=postgres
DB_PORT=5432

# HTTPS (activar tras obtener certificado SSL)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu@email.com
EMAIL_HOST_PASSWORD=<app-password-gmail>

# Stripe
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Superusuario inicial (el entrypoint lo crea automáticamente si no existe)
DJANGO_SUPERUSER_EMAIL=admin@tudominio.com
DJANGO_SUPERUSER_PASSWORD=<contraseña-muy-segura>
```

**Generar SECRET_KEY segura:**
```bash
python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#\$%^&*') for _ in range(50)))"
```

### Actualizar nginx con tu dominio

Editar `docker/nginx/django.conf` y descomentar el bloque HTTPS cambiando
`frameffx.online` por tu dominio real en:
- `server_name`
- `ssl_certificate`  
- `ssl_certificate_key`

---

## 🔐 SSL con Let's Encrypt

### Fase 1 — Obtener certificado (ACME Challenge)

```bash
# Crear directorios necesarios
mkdir -p docker/certbot/conf docker/certbot/www

# Levantar nginx en HTTP para el ACME challenge
docker compose -f docker/docker-compose.prod.yml up -d nginx

# Obtener certificado
docker run --rm \
  -v "$(pwd)/docker/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/docker/certbot/www:/var/www/certbot" \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d tudominio.com \
  -d www.tudominio.com \
  --email tu@email.com \
  --agree-tos \
  --non-interactive
```

### Fase 2 — Activar HTTPS en nginx

Descomentar el bloque `server { listen 443 ssl ... }` en `docker/nginx/django.conf`
y añadir redirección 301 en el bloque HTTP:

```nginx
location / {
    return 301 https://$host$request_uri;
}
```

---

## 🐳 Despliegue con Docker

### Iniciar servicios

```bash
docker compose -f docker/docker-compose.prod.yml up -d --build
```

### Ver logs

```bash
docker compose -f docker/docker-compose.prod.yml logs -f web
```

### Ejecutar comandos Django manualmente

```bash
# Migraciones (el entrypoint.sh las ejecuta automáticamente al arrancar)
docker compose -f docker/docker-compose.prod.yml exec web python manage.py migrate

# Crear superusuario manualmente (solo si no se definieron DJANGO_SUPERUSER_* en .env.prod)
docker compose -f docker/docker-compose.prod.yml exec web python manage.py createsuperuser

# Ver si el superusuario ya fue creado por el entrypoint
docker compose -f docker/docker-compose.prod.yml logs web | grep -i superusuario

# Recopilar estáticos (el entrypoint.sh lo ejecuta automáticamente)
docker compose -f docker/docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## 📦 Scripts de automatización

```bash
# Primer despliegue completo (recomendado)
bash scripts/setup_prod.sh

# Actualizar la aplicación (git pull + rebuild)
bash scripts/deploy.sh

# Renovar certificado SSL
bash scripts/ssl_renew.sh

# Inicializar BD manualmente (si entrypoint falló)
bash scripts/init_db.sh
```

### Renovación SSL automática via cron

```bash
sudo crontab -e
# Añadir (renovar cada domingo a las 3 AM):
0 3 * * 0 /ruta/al/proyecto/scripts/ssl_renew.sh >> /var/log/ssl_renew.log 2>&1
```

---

## 🔄 Actualizar aplicación

```bash
# Pull cambios y rebuild
git pull origin main
docker compose -f docker/docker-compose.prod.yml down
docker compose -f docker/docker-compose.prod.yml up -d --build
```

---

## 📊 Monitoreo

```bash
# Estado de contenedores
docker compose -f docker/docker-compose.prod.yml ps

# Logs en tiempo real
docker compose -f docker/docker-compose.prod.yml logs -f

# Estadísticas de recursos
docker stats
```

---

## 🆘 Troubleshooting

### Los contenedores no inician

```bash
docker compose -f docker/docker-compose.prod.yml logs web postgres nginx
docker compose -f docker/docker-compose.prod.yml restart
```

### Problemas de conexión a BD

```bash
docker compose -f docker/docker-compose.prod.yml ps postgres
docker compose -f docker/docker-compose.prod.yml logs postgres
# Verificar variables de entorno del contenedor web:
docker compose -f docker/docker-compose.prod.yml exec web env | grep DB
```

### CSS no carga (página sin estilos)

```bash
# Verificar que collectstatic se ejecutó correctamente:
docker compose -f docker/docker-compose.prod.yml exec web ls /code/staticfiles/
docker compose -f docker/docker-compose.prod.yml exec nginx ls /code/staticfiles/
# Si está vacío, forzar:
docker compose -f docker/docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker/docker-compose.prod.yml restart nginx
```

### Bucle de redirecciones (ERR_TOO_MANY_REDIRECTS)

Ocurre si `SECURE_SSL_REDIRECT=True` sin SSL activo todavía.

```bash
# Cambiar en .env.prod:
SECURE_SSL_REDIRECT=False
# Reiniciar:
docker compose -f docker/docker-compose.prod.yml restart web
```

### SSL no funciona

```bash
# Verificar que el dominio apunta al servidor
nslookup tudominio.com
# Verificar puerto 80 accesible
curl http://tudominio.com/.well-known/acme-challenge/test
# Si usas UFW:
sudo ufw allow 80 && sudo ufw allow 443
# Verificar certificado
ls -la docker/certbot/conf/live/tudominio.com/
```

### Error 403 en formularios (CSRF)

Django 4.0+ requiere `CSRF_TRUSTED_ORIGINS` configurado. En este proyecto se genera automáticamente a partir de `ALLOWED_HOSTS` (ver `settings.py`), por lo que basta con que `ALLOWED_HOSTS` incluya el dominio correcto:

```env
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
```

### El superusuario no se creó automáticamente

El `entrypoint.sh` crea el superusuario solo si `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD` están definidos en `.env.prod`. Si se omitieron:

```bash
# Crear manualmente:
docker compose -f docker/docker-compose.prod.yml exec web python manage.py createsuperuser

# O verificar si las variables están en el contenedor:
docker compose -f docker/docker-compose.prod.yml exec web env | grep SUPERUSER
```

---

## 📝 Estructura de carpetas

```
proyecto-frameffx/
├── docker/
│   ├── Dockerfile              (imagen desarrollo)
│   ├── Dockerfile.prod         (imagen producción — multi-stage)
│   ├── docker-compose.yml      (base mínima)
│   ├── docker-compose.override.yml  (desarrollo local)
│   ├── docker-compose.prod.yml (producción completa)
│   ├── entrypoint.sh           (migrate + collectstatic + gunicorn)
│   ├── nginx/
│   │   ├── nginx.conf          (config global)
│   │   └── django.conf         (virtual host HTTP/HTTPS)
│   └── certbot/
│       ├── conf/               (certificados SSL — NO versionar)
│       └── www/                (archivos ACME challenge)
├── scripts/
│   ├── setup_prod.sh           (primer despliegue automatizado)
│   ├── deploy.sh               (actualizar aplicación)
│   ├── ssl_renew.sh            (renovar certificado)
│   ├── init_db.sh              (inicializar BD manualmente)
│   └── frameffx.service        (systemd service opcional)
├── .env.example                (plantilla — copiar a .env / .env.prod)
├── .env                        (desarrollo — NO versionar)
├── .env.prod                   (producción — NO versionar)
└── requirements.txt
```

---

## 🔒 Seguridad

- ✅ Variables sensibles en `.env.prod` (en `.gitignore`, nunca versionar)
- ✅ SSL/TLS con Let's Encrypt (TLSv1.2 + TLSv1.3)
- ✅ PostgreSQL no expuesto al exterior (solo accesible en red Docker interna)
- ✅ Puerto 8000 de Gunicorn no expuesto (nginx hace proxy inverso)
- ✅ `DEBUG = False` en producción
- ✅ `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` configurados
- ✅ `SECURE_PROXY_SSL_HEADER` configurado para Django detrás de Nginx
- ✅ Headers de seguridad en Nginx (HSTS, X-Frame-Options, etc.)
- ✅ Rate limiting activo en Nginx (`limit_req zone=general burst=30 nodelay`)
- ✅ Superusuario creado desde variables de entorno (sin credenciales hardcodeadas)
- ✅ `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'` en producción (registros verificados)

---

## 📞 Referencias

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
