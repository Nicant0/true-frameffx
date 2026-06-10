# FrameffX — Inicio rápido en un ordenador nuevo

Guía paso a paso para tener el proyecto corriendo desde cero.
Tiempo estimado: ~5 minutos.

---

## Requisitos previos

| Herramienta | Versión mínima | Descarga |
|-------------|----------------|----------|
| Python      | 3.11+          | https://www.python.org/downloads/ |
| Git         | cualquiera     | https://git-scm.com/ |
| Pillow deps | —              | (se instala solo con pip) |

> En Windows: durante la instalación de Python, marca la casilla
> **"Add Python to PATH"** antes de continuar.

---

## 1. Clonar el repositorio

```bash
git clone <URL-del-repositorio>
cd frameffx-de-main/proyecto-frameffx
```

---

## 2. Crear y activar el entorno virtual

### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Si PowerShell da error de ejecución de scripts:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Luego repite el comando de activación.

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

El prompt debería mostrar `(.venv)` al inicio — eso confirma que está activo.

---

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 4. Crear el archivo de variables de entorno

Crea un archivo llamado `.env` en la carpeta `proyecto-frameffx/` con este contenido:

```env
SECRET_KEY=django-insecure-clave-de-desarrollo-local
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

> Para la demo del TFG, los valores de arriba son suficientes.
> El proyecto funciona sin Stripe ni claves externas en modo local.

---

## 5. Aplicar migraciones (crear la base de datos)

```bash
python manage.py migrate
```

---

## 6. Cargar la base de datos completa de demostración

Hemos guardado el estado exacto de la plataforma (catálogo de productos, clases, usuarios y configuración) en un archivo prefabricado (`demo_data.json`) que se encuentra en el repositorio junto a la carpeta de imágenes (`media/`).
Para cargar toda esta información en tu nueva base de datos local de golpe, ejecuta:

```bash
python manage.py loaddata demo_data.json
```

Deberías ver un mensaje de confirmación parecido a:
```
Installed 200 object(s) from 1 fixture(s)
```

---

## 7. Crear un superusuario (administrador)

```bash
python manage.py createsuperuser
```

Introduce un nombre de usuario, email y contraseña cuando lo pida.

---

## 8. Arrancar el servidor

```bash
python manage.py runserver
```

Abre el navegador en: **http://127.0.0.1:8000**

Panel de administración: **http://127.0.0.1:8000/admin**

---

## Resumen de comandos (todo junto)

```bash
git clone <URL>
cd frameffx-de-main/proyecto-frameffx

python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt

# Crear .env con SECRET_KEY, DEBUG=True, ALLOWED_HOSTS=localhost,127.0.0.1

python manage.py migrate
python manage.py loaddata demo_data.json   # carga el catálogo completo de demo
python manage.py createsuperuser
python manage.py runserver
```

---

## Solución de problemas frecuentes

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| `ModuleNotFoundError: No module named 'django'` | Entorno virtual no activo | Ejecutar el paso de activación (.venv) |
| `Error: That port is already in use` | Puerto 8000 ocupado | `python manage.py runserver 8080` |
| Las imágenes no aparecen | Falta la carpeta `media/` | Ya está en el repo; si falta, ejecuta `seed_products` |
| `OperationalError: no such table` | Migraciones no aplicadas | `python manage.py migrate` |
| Scripts de PS1 bloqueados | Política de ejecución de PowerShell | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
