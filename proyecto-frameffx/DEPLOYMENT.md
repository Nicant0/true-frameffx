# FrameffX - Deployment Guide

Guía completa para desplegar FrameffX en un VPS con dominio.

## 📋 Requisitos

- VPS con Ubuntu 20.04+ o similar
- Docker y Docker Compose instalados
- Git instalado
- Dominio apuntando al VPS
- Acceso SSH al servidor

## 🚀 Instalación Inicial

### 1. Conectarse al VPS

```bash
ssh user@your-vps-ip
```

### 2. Instalar dependencias

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Instalar Git
sudo apt install -y git

# Instalar Certbot para SSL
sudo apt install -y certbot python3-certbot-nginx
```

### 3. Clonar el repositorio

```bash
git clone https://github.com/your-repo/frameffx.git
cd frameffx
```

### 4. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env.prod

# Editar con tus valores
nano .env.prod
```

**Variables importantes a configurar:**

```env
SECRET_KEY=your-very-secure-random-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_PASSWORD=very-secure-password-here
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 5. Generar SECRET_KEY segura

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Crear directorios necesarios

```bash
mkdir -p docker/certbot/conf docker/certbot/www scripts
chmod +x scripts/*.sh docker/entrypoint.sh
```

### 7. Actualizar dominio en Nginx

Editar `docker/nginx/django.conf` y cambiar:

```nginx
server_name yourdomain.com www.yourdomain.com;

ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
```

## 🔐 SSL con Let's Encrypt

### Obtener certificado inicial

```bash
# Crear directorio temporal
sudo mkdir -p docker/certbot/www

# Ejecutar certbot
docker run --rm -v "$(pwd)/docker/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/docker/certbot/www:/var/www/certbot" \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email your-email@example.com \
  --agree-tos \
  --non-interactive
```

## 🐳 Despliegue con Docker

### Iniciar servicios

```bash
cd docker
docker-compose -f docker-compose.prod.yml up -d
```

### Ver logs

```bash
docker-compose -f docker-compose.prod.yml logs -f web
```

### Ejecutar comandos Django

```bash
# Migraciones
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Crear superusuario
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Recopilar estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## 📦 Scripts de Automatización

### Deploy automático

```bash
# Hacer scripts ejecutables
chmod +x scripts/*.sh

# Ejecutar deploy
./scripts/deploy.sh
```

### Renovar SSL automáticamente

```bash
# Crear tarea cron
sudo crontab -e

# Agregar línea (renovar cada día a las 3 AM):
0 3 * * * /ruta/al/proyecto/scripts/ssl_renew.sh
```

### Inicializar base de datos

```bash
./scripts/init_db.sh
```

## 🔄 Actualizar aplicación

```bash
# Pull cambios
git pull origin main

# Rebuild y restart
docker-compose -f docker/docker-compose.prod.yml down
docker-compose -f docker/docker-compose.prod.yml up -d --build
```

## 📊 Monitoreo

### Ver estado de contenedores

```bash
docker-compose -f docker/docker-compose.prod.yml ps
```

### Ver logs en tiempo real

```bash
docker-compose -f docker/docker-compose.prod.yml logs -f
```

### Estadísticas de recursos

```bash
docker stats
```

## 🆘 Troubleshooting

### Los contenedores no inician

```bash
# Ver logs detallados
docker-compose -f docker/docker-compose.prod.yml logs web postgres nginx

# Reiniciar todo
docker-compose -f docker/docker-compose.prod.yml restart
```

### Problemas de conexión a BD

```bash
# Verificar que PostgreSQL está corriendo
docker-compose -f docker/docker-compose.prod.yml ps postgres

# Ver logs de PostgreSQL
docker-compose -f docker/docker-compose.prod.yml logs postgres
```

### SSL no funciona

```bash
# Verificar certificado
ls -la docker/certbot/conf/live/yourdomain.com/

# Reinstalar certificado
./scripts/ssl_renew.sh
```

## 📝 Estructura de carpetas

```
proyecto-frameffx/
├── docker/
│   ├── Dockerfile (desarrollo)
│   ├── Dockerfile.prod (producción)
│   ├── docker-compose.yml
│   ├── docker-compose.override.yml
│   ├── docker-compose.prod.yml
│   ├── entrypoint.sh
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── django.conf
│   └── certbot/
│       ├── conf/ (certificados SSL)
│       └── www/
├── scripts/
│   ├── deploy.sh
│   ├── init_db.sh
│   └── ssl_renew.sh
├── .env.example
├── .env.prod (no versionar)
├── requirements.txt
└── ...
```

## 🔒 Seguridad

- ✅ Variables sensibles en `.env.prod` (nunca versionar)
- ✅ SSL/TLS con Let's Encrypt
- ✅ PostgreSQL con contraseña segura
- ✅ DEBUG = False en producción
- ✅ ALLOWED_HOSTS configurado
- ✅ Headers de seguridad en Nginx
- ✅ Rate limiting habilitado

## 📞 Soporte

Para más información, consultar la documentación oficial:
- [Django Deployment](https://docs.djangoproject.com/en/5.2/howto/deployment/)
- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
