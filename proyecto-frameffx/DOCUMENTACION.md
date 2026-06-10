# Documentación Técnica Completa — Proyecto FrameffX

> **Proyecto**: FrameffX — Plataforma de e-learning y marketplace de productos digitales  
> **Framework**: Django 5.2  
> **Python**: 3.11+  
> **Base de datos**: SQLite (desarrollo) / PostgreSQL (producción)  
> **Estado**: Funcional con datos de demostración (`demo_data.json`)

---

## Índice

1. [Visión General del Proyecto](#1-visión-general-del-proyecto)
2. [Arquitectura y Stack Tecnológico](#2-arquitectura-y-stack-tecnológico)
3. [Estructura de Directorios](#3-estructura-de-directorios)
4. [La Configuración Central (FrameffX/)](#4-la-configuración-central-frameffx)
5. [El Sistema de Enrutamiento (urls.py)](#5-el-sistema-de-enrutamiento-urlspy)
6. [App: Usuarios (users)](#6-app-usuarios-users)
7. [App: Autenticación y Login (login)](#7-app-autenticación-y-login-login)
8. [App: Clases Virtuales (teachings)](#8-app-clases-virtuales-teachings)
9. [App: Marketplace de Productos (products)](#9-app-marketplace-de-productos-products)
10. [App: Reservas y Pagos de Clases (bookings)](#10-app-reservas-y-pagos-de-clases-bookings)
11. [App: Vistas Generales (common)](#11-app-vistas-generales-common)
12. [La API REST](#12-la-api-rest)
13. [El Sistema de Pagos con Stripe](#13-el-sistema-de-pagos-con-stripe)
14. [El Sistema de Plantillas (Templates)](#14-el-sistema-de-plantillas-templates)
15. [El Panel de Administración (Django Admin)](#15-el-panel-de-administración-django-admin)
16. [Despliegue con Docker](#16-despliegue-con-docker)
17. [Comandos de Gestión (Management Commands)](#17-comandos-de-gestión-management-commands)
18. [Variables de Entorno y Seguridad](#18-variables-de-entorno-y-seguridad)
19. [Flujo Completo de un Usuario](#19-flujo-completo-de-un-usuario)

---

## 1. Visión General del Proyecto

**FrameffX** es una plataforma web multifuncional que opera como dos servicios integrados en un mismo sistema:

1. **E-learning / Mentorías**: Los usuarios pueden ver un catálogo de clases virtuales (docentes, masterclasses, mentorías), reservar su plaza y pagar por ella. El sistema gestiona el estado de cada reserva en tiempo real.

2. **Marketplace Digital**: Los usuarios pueden comprar y descargar archivos digitales (presets de edición, plugins, guías, archivos de proyecto). El sistema controla estrictamente el número de veces que cada comprador puede descargar el archivo comprado.

La plataforma está diseñada para que el mismo administrador pueda:
- Gestionar el catálogo de clases y productos desde interfaces dedicadas.
- Consultar métricas de negocio (ingresos, reservas, usuarios activos) en tiempo real desde un panel de control propio.
- Permitir que los usuarios se registren clásicamente o usando su cuenta de Google (OAuth 2.0).

---

## 2. Arquitectura y Stack Tecnológico

### Tipo de Arquitectura

La aplicación sigue una arquitectura **Monolítica Híbrida**: el mismo servidor Django genera el HTML y también expone una API REST. Esto permite que la plataforma funcione como un sitio web tradicional de renderizado en servidor (SSR) y, al mismo tiempo, pueda ser consumida como backend puro por aplicaciones móviles futuras.

```
Petición del Navegador
        │
        ▼
┌──────────────────────┐       ┌─────────────────────┐
│   Nginx (Proxy)      │──────▶│   Gunicorn (WSGI)   │
└──────────────────────┘       └──────────┬──────────┘
                                          │
                                          ▼
                               ┌──────────────────────┐
                               │   Django Application  │
                               │  ┌────────────────┐  │
                               │  │   urls.py       │  │
                               │  └───────┬────────┘  │
                               │          │            │
                               │  ┌───────▼────────┐  │
                               │  │   Views / API   │  │
                               │  └───────┬────────┘  │
                               │          │            │
                               │  ┌───────▼────────┐  │
                               │  │   Models / ORM  │  │
                               │  └───────┬────────┘  │
                               └──────────┼────────────┘
                                          │
                               ┌──────────▼──────────┐
                               │  SQLite / PostgreSQL  │
                               └─────────────────────┘
```

### Stack Tecnológico Completo

| Capa | Tecnología | Motivo |
|---|---|---|
| Backend Framework | **Django 5.2** | Baterías incluidas, ORM potente, ecosistema maduro |
| Lenguaje | **Python 3.11+** | Rendimiento mejorado, tipado moderno |
| Frontend | **Django Templates + Bootstrap 5** | Renderizado server-side, sin necesidad de SPA |
| Formularios | **crispy_forms + crispy_bootstrap5** | Bootstrap integrado automáticamente en formularios |
| API REST | **Django Rest Framework (DRF)** | Estándar del sector para APIs en Django |
| Auth API | **Djoser + JWT** | Gestión de tokens estándar para APIs |
| Auth Social | **django-allauth** | Soporte OAuth 2.0 (Google) con pocas líneas de config |
| Pagos | **Stripe Checkout** | Pasarela líder, gestión de webhooks robusta |
| BD Desarrollo | **SQLite** | Sin instalación extra, ideal para trabajo local |
| BD Producción | **PostgreSQL 16** | Robustez, concurrencia, escalabilidad |
| Servidor Web | **Gunicorn + Nginx** | Configuración estándar de producción para Django |
| Contenedores | **Docker + Docker Compose** | Reproducibilidad, independencia del entorno |
| SSL | **Let's Encrypt (Certbot)** | Certificados HTTPS gratuitos y renovación automática |
| Variables secretas | **python-dotenv** | Separación de código y configuración sensible |

---

## 3. Estructura de Directorios

```
proyecto-frameffx/
│
├── FrameffX/               # Core del proyecto (configuración y enrutamiento)
│   ├── settings.py         # Toda la configuración global
│   ├── urls.py             # Router principal de URLs
│   ├── asgi.py / wsgi.py   # Puntos de entrada ASGI y WSGI
│   └── __init__.py
│
├── users/                  # App: Sistema de usuarios personalizado
├── login/                  # App: Vistas de login/logout
├── teachings/              # App: Catálogo de clases y mentorías + API
├── products/               # App: Marketplace de archivos digitales
├── bookings/               # App: Reservas de clases y checkout
├── common/                 # App: Vistas compartidas (landing, dashboard admin)
├── ads/                    # App: Módulo de anuncios (presente pero secundario)
│
├── templates/              # Plantillas HTML globales, organizadas por contexto
│   ├── portfolio/          # Vistas principales (landing, home, login, etc.)
│   ├── products/           # Vistas admin de productos
│   ├── users/              # Vistas de perfil y gestión de usuarios
│   ├── account/            # Plantillas de django-allauth (confirmación, etc.)
│   └── socialaccount/      # Plantillas de OAuth (errores, cancelaciones)
│
├── static/                 # Archivos CSS, JS e imágenes del proyecto
├── staticfiles/            # Destino de collectstatic para producción
├── media/                  # Archivos subidos por el admin (portadas, archivos ZIP)
│
├── docker/                 # Infraestructura de contenedores
│   ├── Dockerfile          # Imagen para desarrollo
│   ├── Dockerfile.prod     # Imagen optimizada de producción (multi-stage)
│   ├── docker-compose.yml  # Compose para desarrollo
│   ├── docker-compose.prod.yml # Compose para producción (web + postgres + nginx)
│   ├── entrypoint.sh       # Script de arranque: migra, colecta estáticos, levanta Gunicorn
│   └── nginx/              # Configuración de Nginx como proxy inverso
│
├── scripts/                # Scripts de automatización (deploy, SSL, init_db)
│
├── .env                    # Variables de entorno (NO se sube a Git)
├── .env.example            # Plantilla documentada de las variables necesarias
├── .gitignore              # Exclusiones de control de versiones
├── manage.py               # CLI de Django
├── requirements.txt        # Dependencias de producción
├── requirements-dev.txt    # Dependencias adicionales de desarrollo
└── demo_data.json          # Fixture completo para demo (catálogo + usuarios)
```

---

## 4. La Configuración Central (FrameffX/)

### `settings.py` — El Cerebro de la Configuración

Este archivo controla absolutamente todo el comportamiento de Django. Se ha diseñado para ser **"environment-aware"**: su comportamiento cambia automáticamente según el entorno (desarrollo vs. producción) sin modificar el código, solo cambiando el `.env`.

#### Carga de variables de entorno

```python
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
```

Se usa `try/except` al importar `python-dotenv`. Esto hace que el proyecto no falle si alguien no tiene instalada la librería (en entornos donde las variables se inyectan directamente, como Docker o sistemas CI/CD).

#### Selección dinámica de base de datos

```python
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')

if DB_ENGINE == 'django.db.backends.postgresql':
    DATABASES = { ... } # PostgreSQL (Producción)
else:
    DATABASES = { ... } # SQLite (Desarrollo)
```

Con una sola variable de entorno (`DB_ENGINE`), el mismo código fuente sirve tanto en el portátil de desarrollo como en el VPS de producción. No hay que tocar el `settings.py` nunca para cambiar de base de datos.

#### INSTALLED_APPS: Aplicaciones Registradas

```python
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    'django.contrib.sites',     # Necesario para allauth y OAuth
    # Librerías de terceros
    'rest_framework',           # API REST
    'rest_framework.authtoken', # Tokens de API
    'crispy_forms',             # Formularios bonitos
    'crispy_bootstrap5',        # Integración con Bootstrap 5
    'allauth',                  # Autenticación avanzada
    'allauth.account',          # Login/Register por email
    'allauth.socialaccount',    # OAuth genérico
    'allauth.socialaccount.providers.google', # Google OAuth
    'djoser',                   # Endpoints JWT/Token para la API
    # Apps propias del proyecto
    'ads', 'bookings', 'teachings', 'common', 'users', 'products',
]
```

#### Modelo de usuario personalizado

```python
AUTH_USER_MODEL = 'users.Usuario'
```

Esta es quizás la línea más importante de todo `settings.py`. Le dice a Django que use el modelo `Usuario` personalizado en lugar del modelo `auth.User` de Django. **Esto debe declararse antes de crear cualquier migración**, ya que afecta a todas las relaciones en la base de datos.

#### Configuración de Allauth y Google OAuth

```python
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http' if DEBUG else 'https'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'prompt': 'select_account', # Fuerza el selector de cuentas de Google
        },
    }
}

SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
```

El atributo `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True` es especialmente importante: si un usuario que se registró con email y contraseña luego intenta entrar con Google usando el mismo email, Django los conecta automáticamente en lugar de crear una cuenta duplicada.

`SOCIALACCOUNT_LOGIN_ON_GET = True` elimina la pantalla de confirmación intermedia de allauth que normalmente aparece antes de hacer el OAuth.

#### Seguridad en Producción

```python
if not DEBUG:
    SECURE_SSL_REDIRECT = ...
    SESSION_COOKIE_SECURE = ...
    CSRF_COOKIE_SECURE = ...
    X_FRAME_OPTIONS = 'DENY'
```

Todos los headers de seguridad HTTP (HSTS, cookies seguras, protección de clickjacking) solo se activan cuando `DEBUG = False`, evitando problemas en desarrollo local.

---

## 5. El Sistema de Enrutamiento (urls.py)

El archivo `FrameffX/urls.py` actúa como la **tabla de control de tráfico** de toda la aplicación. Cada URL que llega al servidor es comparada contra esta lista de patrones y despachada a la vista correspondiente.

### Organización de las URLs

Las URLs están agrupadas en bloques semánticos con comentarios claros:

```python
urlpatterns = [
    # Panel de Django Admin
    path('admin/', admin.site.urls),
    
    # Panel analítico propio (solo Staff)
    path('dashboard-admin/', AdminDashboardView.as_view(), name='admin_dashboard'),

    # Landing pública
    path('', LandingView.as_view(), name='landing'),

    # ── Autenticación ────────────────
    path('login/', LoginFormView.as_view(), name='site_login'),
    path('accounts/login/', LoginFormView.as_view(), name='accounts_login'),
    path('logout/', Logout.as_view(), name="site_logout"),
    path('signup/', views.SignupView.as_view(), name='signup'),

    # ── Core ─────────────────────────
    path('home/', showTeachings.as_view(), name='home'),
    path('products/', include('products.urls')),     # Namespace 'products:'

    # ── CRUD de Clases ────────────────
    path('teachings/create/', TeachingCreateView...),
    path('teachings/<int:pk>/', TeachingDetailView...),
    path('teachings/<int:pk>/update/', TeachingUpdateView...),
    path('teachings/<int:pk>/delete/', TeachingDeleteView...),

    # ── CRUD de Usuarios ─────────────
    path('perfil/', views.UserProfileView..., name='user_profile'),
    path('usuarios/', views.UsuariosListView..., name='usuarios_list'),
    ...

    # ── Reservas ─────────────────────
    path('bookings/create/', ReservaCreateView...),
    path('bookings/<int:pk>/cancel/', ReservaCancelView...),
    path('bookings/<int:pk>/checkout/', ReservaCheckoutView...),
    path('bookings/success/', ReservaSuccessView...),

    # ── OAuth y allauth ───────────────
    path('accounts/', include('allauth.urls')),

    # ── API REST ──────────────────────
    path('api/', include(router.urls)),             # DRF Router
    path('api/auth/', include('djoser.urls')),      # Auth Djoser
    path('api/auth/', include('djoser.urls.jwt')),  # JWT Tokens
    path('api/token/refresh/', TokenRefreshView...), # Refresh JWT
]
```

### El DRF Router

```python
router = routers.DefaultRouter()
router.register('teachings', TeachingViewSet, basename='teachings')
router.register('teachings-auth', TeachingAuthenticatedListViewSet, basename='teachings-auth')
router.register('teachings-crud', TeachingCRUDView, basename='teachings-crud')
```

El `DefaultRouter` genera automáticamente los endpoints estándar de una API REST (`GET /api/teachings/`, `GET /api/teachings/{id}/`) sin necesidad de escribir cada path a mano. Los tres ViewSets registrados tienen distintos niveles de permiso (ver sección API REST).

### Servido de archivos estáticos y media en desarrollo

```python
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=...)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

En producción, Nginx se encarga de servir los archivos estáticos y de media directamente (mucho más eficiente). En desarrollo local, Django los sirve él mismo para que no sea necesario configurar Nginx.

---

## 6. App: Usuarios (users)

### El Problema Resuelto

Django por defecto usa `username` como identificador principal para el login. En FrameffX, el flujo de registro y autenticación se basa **exclusivamente en el email**, que es el estándar moderno y elimina la fricción del registro.

### El Modelo `Usuario` (models.py)

```python
class Usuario(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(unique=True)
    
    # Campos de perfil
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    biografia = models.TextField(max_length=500, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)

    activo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'   # ← El email es el identificador
    REQUIRED_FIELDS = []        # ← Solo el email es obligatorio en creación
    
    objects = UsuarioManager()
```

- **`AbstractBaseUser`**: Herencia que da control total sobre el modelo. Django no impone ninguna estructura de campos.
- **`PermissionsMixin`**: Añade los campos de permisos de Django (`is_superuser`, `groups`, `user_permissions`), necesarios para que el panel de Admin funcione correctamente.
- **`username`**: Se mantiene como campo `null=True` y `blank=True` para que sirva como apodo/nombre visible en la interfaz sin ser obligatorio.
- **`foto_perfil`**: Se sube al directorio `media/perfiles/`, gestionado por Django Media Files.

### El `UsuarioManager` (models.py)

```python
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Encripta con PBKDF2
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
```

El manager personalizado es obligatorio cuando se hereda de `AbstractBaseUser`. Garantiza que `python manage.py createsuperuser` funcione correctamente pidiendo solo email en lugar de username.

### Los Formularios (forms.py)

#### `RegistroForm`
Formulario de registro público que realiza tres validaciones encadenadas:

1. **`clean_email()`**: Consulta la base de datos para verificar que el email no está ya registrado. Normaliza el email a minúsculas antes de guardar.
2. **`clean_password1()`**: Ejecuta `validate_password()` de Django, que aplica todos los validadores definidos en `AUTH_PASSWORD_VALIDATORS` (longitud mínima, no muy común, no solo números).
3. **`clean()`**: Verifica que `password1` y `password2` coincidan exactamente.

El método `save()` crea el `Usuario` con `is_active=True` y `is_staff=False`. Llama a `user.set_password(password)` que encripta la contraseña con **PBKDF2-SHA256** antes de guardarla en la base de datos. Nunca se almacena la contraseña en texto plano.

#### `UserProfileForm`
```python
class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True  # No se puede cambiar el email
```

El campo `email` se deshabilita en el formulario de perfil para evitar que los usuarios cambien su email (que es el identificador único de su cuenta), previniendo posibles conflictos de autenticación o suplantaciones.

### Las Vistas (views.py)

#### `SignupView` — Registro con login automático

```python
class SignupView(TemplateView):
    def post(self, request, *args, **kwargs):
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user,
                  backend="django.contrib.auth.backends.ModelBackend")
            return redirect("home")
```

En lugar de usar `CreateView`, se usa `TemplateView` con un método `post` manual. Esto permite llamar a `login()` inmediatamente después de registrar al usuario, evitando que tenga que iniciar sesión por segunda vez tras registrarse. El parámetro `backend` es obligatorio cuando hay múltiples backends de autenticación registrados (allauth + Django estándar).

#### `UserProfileView` — Edición de perfil
```python
class UserProfileView(LoginRequiredMixin, UpdateView):
    def get_object(self, queryset=None):
        return self.request.user  # Siempre edita el usuario actual
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pedidos_completados"] = get_pedidos_completados_para_usuario(self.request.user)
        return context
```

`get_object()` sobrescrito garantiza que el usuario siempre edita **su propio perfil**, no el de otro. Inyecta también los pedidos completados para mostrar el historial de compras en la página de perfil.

### Los Mixins de Seguridad (mixins.py)

```python
class StaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("No tienes permisos")
        return super().dispatch(request, *args, **kwargs)
```

`StaffRequiredMixin` es un mixin de autorización reutilizable que se añade a cualquier vista que requiera privilegios de administrador. Hereda de `LoginRequiredMixin` (que gestiona el caso de usuarios no autenticados) y añade la comprobación de `is_staff`. Se usa en las vistas CRUD de clases, productos y usuarios.

```python
class SetPasswordMixin:
    def form_valid(self, form):
        usuario = form.save(commit=False)
        password = self.request.POST.get(self.password_field)
        if password:
            usuario.set_password(password)  # Siempre encripta antes de guardar
        usuario.save()
        return super().form_valid(form)
```

`SetPasswordMixin` permite que los formularios de Admin de creación/edición de usuarios tengan un campo de contraseña que se encripta correctamente con `set_password()`. `commit=False` guarda los datos del formulario sin hacer el `INSERT` en la base de datos todavía, permitiendo modificar el objeto antes del guardado real.

---

## 7. App: Autenticación y Login (login)

Esta app contiene las vistas de autenticación clásica de Django, personalizadas para el flujo específico de FrameffX.

### `LoginFormView`

```python
class LoginFormView(LoginView):
    template_name = "portfolio/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return str(self.success_url)  # Ignora el ?next= del querystring
```

Hereda de `LoginView` de Django, que ya implementa toda la lógica de autenticación. Se sobrescriben dos comportamientos:
1. **`redirect_authenticated_user = True`**: Si un usuario ya autenticado intenta visitar `/login/`, es redirigido al home automáticamente.
2. **`get_success_url()`**: Ignora el parámetro `?next=` que Django añade automáticamente. Esto previene que usuarios maliciosos usen el parámetro `next` para redirigir a URLs externas (Open Redirect) o para romper el flujo esperado de la interfaz.

### `Logout`

```python
class Logout(LogoutView):
    next_page = reverse_lazy("site_login")

    def get_success_url(self):
        return str(self.next_page)  # Siempre vuelve al login
```

Similar a `LoginFormView`, sobrescriben `get_success_url()` para garantizar que siempre vuelva a la pantalla de login interna, ignorando cualquier URL de redirección externa inyectada.

### OAuth con Google (django-allauth)

La autenticación con Google no requiere código propio en vistas. `django-allauth` expone sus URLs bajo `accounts/` y gestiona todo el flujo OAuth 2.0:

1. El usuario hace clic en "Continuar con Google".
2. `allauth` redirige a Google con los scopes configurados (`profile`, `email`).
3. Google autentifica y redirige de vuelta con un código de autorización.
4. `allauth` intercambia el código por un token y obtiene los datos del perfil.
5. Si el email ya existe en la BD (cuenta creada previamente), los conecta (`SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT`). Si no, crea un nuevo `Usuario`.
6. Redirige a `LOGIN_REDIRECT_URL = '/'` que la `LandingView` detecta y redirige al home.

Las credenciales de Google (Client ID y Client Secret) se gestionan desde el panel de Django Admin en `Sites > Social Applications`, por lo que nunca se hardcodean en el código fuente.

---

## 8. App: Clases Virtuales (teachings)

### El Modelo `Teaching` (models.py)

```python
class Teaching(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    duracion_min = models.PositiveIntegerField()  # Pre-calculado, no derivado

    ESTADOS = [
        ("activa", "Activa"),
        ("cancelada", "Cancelada"),
        ("finalizada", "Finalizada"),
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS, default="activa")

    class Meta:
        ordering = ["start_at"]
        unique_together = ("title", "start_at")  # No dos clases iguales al mismo tiempo

    @property
    def is_active_now(self):
        return self.estado == "activa" and self.start_at > timezone.now()

    @property
    def is_finished_now(self):
        return self.estado == "finalizada" or self.end_at < timezone.now()
```

**Decisión: `duracion_min` precalculado**  
La duración de una clase podría calcularse en cualquier momento como `(end_at - start_at).total_seconds() / 60`. Sin embargo, almacenarla en base de datos tiene ventajas de rendimiento: al mostrar 9 tarjetas de clases en el catálogo paginado, no se ejecutan 9 cálculos de diferencia de fechas en Python por cada petición. Es un trade-off consciente entre redundancia de datos y velocidad de lectura.

**`unique_together = ("title", "start_at")`**  
Garantiza a nivel de base de datos que no puedan existir dos clases con el mismo título y la misma fecha/hora de inicio. Si se intenta insertar un duplicado, la base de datos lanza un `IntegrityError` que las vistas capturan y muestran al administrador como un mensaje de error amigable.

**Propiedades `is_active_now` e `is_finished_now`**  
Son propiedades computadas (decoradas con `@property`) que se pueden usar directamente en los templates de Django con `{{ teaching.is_active_now }}` y en el código Python. Centralizan la lógica de estado temporal para no repetirla en múltiples vistas.

### La Vista Principal: `showTeachings` (views.py)

Esta es la vista más compleja del proyecto porque sirve a **tres tipos de perfiles con experiencias distintas**:

```python
class showTeachings(ListView):
    paginate_by = 9  # 9 clases por página (3 filas de 3 tarjetas)

    def get_template_names(self):
        # Staff ve una plantilla con controles de administración
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return ["portfolio/home.html"]
        # Usuarios y visitantes ven la plantilla del catálogo público
        return ["portfolio/home_user.html"]

    def get_queryset(self):
        user = self.request.user
        # Staff puede ver TODAS las clases (incluso finalizadas o canceladas)
        if user.is_authenticated and user.is_staff:
            queryset = Teaching.objects.all()
        # Usuarios y visitantes solo ven las activas con fecha futura
        else:
            queryset = Teaching.objects.filter(estado="activa", start_at__gt=timezone.now())
        
        # Filtros opcionales por URL querystring (?titulo=...&estado=...&orden=...&dir=...)
        titulo = self.request.GET.get("titulo")
        if titulo:
            queryset = queryset.filter(title__icontains=titulo)
        ...
        return queryset.order_by(campo_orden)
```

**El inyectado de contexto diferenciado:**

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    user = self.request.user
    if user.is_authenticated and not user.is_staff:
        reservas_usuario = Reserva.objects.select_related("clase").filter(
            usuario=user).exclude(estado__in=["cancelada", "caducada"])
        
        context["reservas_ids"] = set(reservas_usuario.values_list("clase_id", flat=True))
        context["reservas_activas"] = reservas_usuario.filter(...)
        context["reservas_finalizadas"] = reservas_usuario.filter(...)
        context["pedidos_completados"] = get_pedidos_completados_para_usuario(user)
    else:
        # Siempre se envían las variables, aunque vacías, para que el template no falle
        context["reservas_ids"] = set()
        context["reservas_activas"] = Reserva.objects.none()
        ...
```

`reservas_ids` es un `set` de IDs de clases que el usuario tiene reservadas. El template Django puede hacer `{% if teaching.id in reservas_ids %}` en O(1) en lugar de O(n) si fuera una lista. El uso de `.select_related("clase")` evita las consultas N+1 al acceder a datos de la clase desde cada reserva.

### CRUD de Clases: Gestión de Errores

Todos los métodos `form_valid()` del CRUD de clases están envueltos en `try/except` para capturar:
- `IntegrityError`: Conflicto de unicidad (`unique_together`). Se informa al admin sin crashear.
- `DatabaseError`: Error genérico de la base de datos. Se informa al admin sin crashear.

```python
def form_valid(self, form):
    try:
        response = super().form_valid(form)
        messages.success(self.request, f"La clase «{self.object.title}» ha sido creada.")
        return response
    except IntegrityError:
        messages.error(self.request, "Error: Ya existe una clase con este título en la misma fecha y hora.")
        return self.form_invalid(form)
```

---

## 9. App: Marketplace de Productos (products)

### Los Modelos (models.py)

La app de productos implementa un **sistema de comercio electrónico normalizado** siguiendo las reglas de diseño de bases de datos transaccionales.

#### `Producto`
```python
class Producto(models.Model):
    TIPOS_PRODUCTO = [
        ("preset", "Preset"), ("guia", "Guía"),
        ("plugin", "Plugin"), ("proyecto", "Archivo de proyecto"),
        ("bundle", "Bundle"),
    ]
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS_PRODUCTO)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    publicado = models.BooleanField(default=True)
    
    archivo_digital = models.FileField(upload_to="productos/archivos/")
    imagen_portada = models.ImageField(upload_to="productos/portadas/")
    max_descargas = models.PositiveSmallIntegerField(default=3)
    
    class Meta:
        unique_together = ("titulo", "tipo")  # No duplicar productos idénticos
```

`max_descargas = 3` como valor por defecto significa que cada comprador puede bajar el archivo 3 veces. Si necesitan más, el administrador puede cambiarlo desde el panel. Esto protege el contenido digital contra la distribución masiva.

#### `Pedido` y `DetallePedido` — La Normalización Contable

Esta es una de las decisiones de diseño más importantes del proyecto. La compra se divide en dos tablas:

```
Pedido (cabecera de la factura)
  │  id, usuario, estado, total, referencia_pago, fecha_creacion
  │
  └─► DetallePedido (líneas de la factura)
          │  pedido, producto, precio_unitario (HISTÓRICO), cantidad
          │
          └─► Descarga (registro de bajadas)
                    detalle, fecha, ip_origen
```

**Por qué el `precio_unitario` histórico:**
Si se guarda solo la referencia al `Producto` en `DetallePedido`, cuando el administrador cambie el precio de un preset de €15 a €20, todos los pedidos anteriores mostrarían €20 en lugar del precio original de €15. Guardando el precio en el momento de la compra (`precio_unitario`), los registros contables son inmutables.

```python
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)  # PROTECT: no borrar si hay pedidos
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)  # Precio histórico
    cantidad = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ("pedido", "producto")  # No duplicar líneas en el mismo pedido
```

`on_delete=models.PROTECT` en la FK de `Producto` es fundamental: impide que un administrador pueda borrar un producto que ya tiene pedidos asociados, que provocaría que los registros del historial de compras de los usuarios quedaran huérfanos.

#### `Descarga` — Control de Acceso a Archivos

```python
class Descarga(models.Model):
    detalle = models.ForeignKey(DetallePedido, on_delete=models.CASCADE, related_name="descargas")
    fecha = models.DateTimeField(auto_now_add=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)

    @classmethod
    def puede_descargar(cls, detalle: DetallePedido) -> bool:
        usadas = cls.objects.filter(detalle=detalle).count()
        return usadas < detalle.producto.max_descargas
```

`puede_descargar()` es un **class method** (se llama en la clase, no en una instancia): `Descarga.puede_descargar(detalle)`. Cuenta los registros de `Descarga` asociados a ese `DetallePedido` y compara con el límite. Si el usuario ya descargó 3 veces y el límite es 3, devuelve `False` y el servidor bloquea la descarga.

### Las Vistas (views.py y checkout_views.py)

#### `showProducts` — Vista pública del marketplace

```python
class showProducts(ListView):
    def get_queryset(self):
        queryset = Producto.objects.filter(publicado=True)  # Solo publicados
        # Ordenación dinámica por querystring (?orden=precio&dir=asc)
        ...
        return queryset.order_by(campo_orden)
```

Solo los productos con `publicado=True` son visibles al público. El admin puede despublicar un producto sin borrarlo para hacer cambios sin interrumpir el catálogo.

#### `DownloadProductView` — Entrega segura del archivo

```python
class DownloadProductView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        detalle_id = kwargs.get('pk')
        # get_object_or_404 valida que el DetallePedido sea del usuario actual
        detalle = get_object_or_404(DetallePedido, pk=detalle_id, pedido__usuario=request.user)
        
        # Comprobación 1: El pedido debe estar completado
        if detalle.pedido.estado != 'completado':
            messages.error(request, "El pedido no está completado.")
            return redirect('home')
        
        # Comprobación 2: No ha superado el límite de descargas
        if not Descarga.puede_descargar(detalle):
            messages.error(request, "Has excedido el límite de descargas permitidas.")
            return redirect('home')
        
        # Registrar la descarga con la IP para trazabilidad
        ip = request.META.get('REMOTE_ADDR')
        Descarga.objects.create(detalle=detalle, ip_origen=ip)
        
        # FileResponse sirve el archivo sin exponer la URL directa
        return FileResponse(producto.archivo_digital.open('rb'),
                            as_attachment=True, filename=...)
```

**Seguridad en la entrega del archivo:** Se usa `FileResponse` en lugar de devolver una URL directa al archivo. Esto significa que el archivo se sirve a través de Django, no directamente desde el sistema de archivos. El usuario nunca ve la URL real del archivo en `media/productos/archivos/`, y si intenta acceder directamente a esa URL, solo puede hacerlo si Django lo ha validado. El `get_object_or_404` con `pedido__usuario=request.user` es el doble seguro: si alguien introduce un ID ajeno, recibe 404 en lugar de acceso no autorizado.

### El Admin de Productos (admin.py)

```python
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "precio", "publicado", "archivo_digital")
    list_editable = ("precio", "publicado")  # Edición inline en el listado
    search_fields = ("titulo", "descripcion")
    list_filter = ("tipo", "publicado")

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ("subtotal",)

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [DetallePedidoInline]  # Líneas de pedido dentro del pedido
```

El uso de `list_editable` permite al administrador cambiar el precio o el estado de publicación de múltiples productos directamente desde el listado sin entrar al detalle. `DetallePedidoInline` muestra las líneas del pedido directamente dentro del formulario del Pedido en el Admin.

---

## 10. App: Reservas y Pagos de Clases (bookings)

### El Modelo `Reserva` (models.py)

```python
class Reserva(models.Model):
    ESTADO_RESERVA_CHOICES = [
        ("pendiente_pago", "Pendiente de pago"),
        ("pendiente",      "Pendiente"),
        ("confirmada",     "Confirmada"),
        ("cancelada",      "Cancelada"),
        ("caducada",       "Caducada"),
    ]
    clase = models.ForeignKey("teachings.Teaching", on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADO_RESERVA_CHOICES, default="pendiente")
    caducidad = models.DateTimeField(null=True, blank=True)
    nota = models.TextField(blank=True)

    class Meta:
        unique_together = ("clase", "usuario")
        db_table = "reservas"
```

**`unique_together = ("clase", "usuario")`**: Restricción de base de datos para que un usuario no pueda tener dos reservas a la misma clase. Es la última línea de defensa contra el doble clic o la doble pestaña del navegador.

**El ciclo de vida de estados:**
```
[Reserva gratuita]  pendiente → confirmada
                                    ↓
[Reserva de pago]   pendiente_pago → confirmada (via Stripe)
                           ↓
                        caducada (si no se paga a tiempo)

[Cualquier estado activo] → cancelada (si el usuario cancela)
```

### Vistas de Reserva (views.py)

#### `ReservaCreateView` — Las 4 Validaciones en Cadena

Esta vista es solo de tipo `POST` (no tiene página GET). Se activa desde el formulario del modal de reserva.

```python
class ReservaCreateView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Regla 1: Los admins no pueden reservar
        if request.user.is_staff:
            messages.error(...)
            return redirect("home")

        # Regla 2: La clase debe existir y estar activa
        clase = get_object_or_404(Teaching, pk=request.POST.get("clase_id"))
        if not clase.is_active_now:
            messages.warning(...)
            return redirect("home")

        # Regla 3: No duplicar reservas activas
        reserva_existente = Reserva.objects.filter(
            clase=clase, usuario=request.user,
        ).exclude(estado__in=["cancelada", "caducada"]).first()
        
        if reserva_existente:
            messages.info(...)
            return redirect("home")

        # Crear la reserva y gestionar errores de BD
        try:
            Reserva.objects.create(clase=clase, usuario=request.user, estado="pendiente")
            messages.success(...)
        except IntegrityError:
            messages.error(...)  # Race condition: dos requests al mismo tiempo
        except DatabaseError:
            messages.error(...)  # Error genérico de BD
```

La comprobación de `IntegrityError` es un seguro ante condiciones de carrera (*race conditions*): dos peticiones POST simultáneas del mismo usuario podrían superar la validación de Python, pero solo una conseguirá insertar en la base de datos; la otra recibirá el `IntegrityError` del `unique_together`.

#### `ReservaCancelView` — Cancelación Segura

```python
def post(self, request, pk, *args, **kwargs):
    reserva = get_object_or_404(Reserva, pk=pk, usuario=request.user)  # Solo SUS reservas
    
    if reserva.estado not in ["pendiente", "confirmada", "pendiente_pago"]:
        messages.warning(...)  # No cancelar reservas ya canceladas o caducadas
        
    if not reserva.clase.is_active_now:
        messages.warning(...)  # No cancelar si la clase ya empezó
    
    reserva.estado = "cancelada"
    reserva.save(update_fields=["estado"])  # UPDATE parcial, más eficiente
```

`update_fields=["estado"]` hace que Django solo actualice el campo `estado` en la base de datos en lugar de hacer un `UPDATE` de toda la fila. Es más eficiente y evita condiciones de carrera donde otro proceso podría estar modificando otro campo al mismo tiempo.

---

## 11. App: Vistas Generales (common)

### `LandingView` — Página de Entrada

```python
class LandingView(TemplateView):
    template_name = "portfolio/landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("products:showProducts")  # Salta al marketplace
        return super().dispatch(request, *args, **kwargs)
```

La landing page es pública y sirve de presentación. Si el usuario ya tiene sesión iniciada, es redirigido directamente al marketplace (`products:showProducts`). Esto evita que usuarios autenticados vean la página de bienvenida cada vez que abren la URL raíz.

### `AdminDashboardView` — Panel Analítico

```python
class AdminDashboardView(StaffRequiredMixin, TemplateView):
    template_name = "portfolio/dashboard_admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # KPIs de usuarios
        context["total_usuarios"] = Usuario.objects.count()
        context["usuarios_activos"] = Usuario.objects.filter(is_active=True).count()
        
        # KPIs de ingresos (solo pedidos completados)
        ingresos = Pedido.objects.filter(estado="completado").aggregate(
            total_sum=Sum("total"))["total_sum"]
        context["total_ingresos"] = ingresos if ingresos else 0
        
        # Últimos 5 pedidos (con JOIN a usuario via select_related)
        context["ultimos_pedidos"] = Pedido.objects.all()\
            .select_related("usuario").order_by("-fecha_creacion")[:5]
        
        # Reservas pendientes de confirmación
        context["reservas_pendientes"] = Reserva.objects.filter(
            estado__in=["pendiente", "pendiente_pago"]).count()
        
        # Próximas 5 clases con reservas (con JOIN a clase y usuario)
        now = timezone.now()
        context["proximas_clases"] = Reserva.objects.filter(
            clase__start_at__gte=now,
            estado__in=["pendiente", "pendiente_pago", "confirmada"],
        ).select_related("clase", "usuario").order_by("clase__start_at")[:5]
        
        return context
```

Cada consulta está optimizada: `aggregate(Sum)` hace el cálculo en la base de datos (más eficiente que traer todos los pedidos y sumarlos en Python), y `select_related` elimina las consultas N+1 al acceder a datos relacionados desde la plantilla.

### `common/utils.py` — Funciones Compartidas

```python
def get_pedidos_completados_para_usuario(user):
    return (
        Pedido.objects
        .filter(usuario=user, estado="completado")
        .prefetch_related("detalles__producto", "detalles__descargas")
        .order_by("-fecha_creacion")
    )
```

Esta función centraliza la consulta del historial de compras. Se usa en dos lugares diferentes (`UserProfileView` y `showTeachings`). Al centralizarla en `utils.py`, cualquier cambio (añadir un filtro, cambiar el orden) se propaga a todos los sitios automáticamente.

`prefetch_related("detalles__producto", "detalles__descargas")` resuelve en una sola consulta adicional todos los productos y las descargas de todos los pedidos, en lugar de hacer una consulta por cada detalle (problema N+1). Es especialmente importante cuando el usuario tiene muchos pedidos.

---

## 12. La API REST

La API REST está integrada en el mismo proyecto Django y comparte los modelos y la base de datos. Está principalmente orientada al catálogo de clases (`teachings`).

### Los ViewSets con Niveles de Permiso

```python
# GET /api/teachings/ — Cualquiera puede leer el catálogo (AllowAny)
class TeachingViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = TeachingSerializer
    pagination_class = paginador_teaching1

# GET /api/teachings-auth/ — Solo usuarios con sesión activa
class TeachingAuthenticatedListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TeachingSerializer

# CRUD completo — Solo administradores
class TeachingCRUDView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = TeachingSerializer
    queryset = Teaching.objects.all()
```

Se definen tres ViewSets con distintos niveles de permiso deliberadamente:
- `TeachingViewSet` (`AllowAny`): Para integraciones externas o apps móviles que solo necesitan leer el catálogo.
- `TeachingAuthenticatedListViewSet` (`IsAuthenticated`): Para mostrar el catálogo a usuarios con cuenta pero con la seguridad de que no es completamente público.
- `TeachingCRUDView` (`IsAdminUser`): Para que un futuro dashboard externo o una app de gestión puedan crear/modificar clases remotamente, sin pasar por la interfaz web.

### El Serializer

```python
class TeachingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teaching
        fields = ['id', 'title', 'price', 'duracion_min', 'estado',
                  'description', 'start_at', 'end_at', 'fecha_creacion']
```

El serializer convierte los objetos Python del modelo `Teaching` en JSON. Al usar `ModelSerializer`, DRF gestiona automáticamente la validación y la conversión de tipos (ej. `DateTimeField` se convierte al formato ISO 8601).

### La Paginación

```python
class paginador_teaching1(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10
```

`page_size_query_param` permite al cliente de la API solicitar un número distinto de resultados por página vía `?page_size=5`. `max_page_size = 10` limita el máximo para evitar peticiones que devuelvan miles de registros y saturen el servidor.

### Autenticación de la API: Djoser + JWT

El sistema `djoser` expone endpoints estándar para gestionar tokens:
- `POST /api/auth/jwt/create/` — Obtener tokens (access + refresh) con email y contraseña.
- `POST /api/auth/jwt/refresh/` — Obtener un nuevo access token usando el refresh token.
- `POST /api/auth/token/login/` — Obtener AuthToken (alternativa a JWT).

---

## 13. El Sistema de Pagos con Stripe

El sistema de pagos es una de las partes más críticas del proyecto. Está implementado en dos flujos paralelos con la misma lógica central: uno para reservas de clases (`bookings/checkout_views.py`) y otro para productos digitales (`products/checkout_views.py`).

### Flujo Completo de un Pago de Reserva

```
Usuario → POST /bookings/<pk>/checkout/
                │
                ▼ (ReservaCheckoutView)
    1. ¿Es staff? → Bloquear
    2. ¿Clase activa? → Validar
    3. ¿Ya tiene reserva? → Reutilizar pendiente o bloquear
    4. Crear Reserva (estado="pendiente_pago")
    5. stripe.checkout.Session.create(...)
                │
                ▼ (Stripe Servers)
    6. Usuario paga en la página de Stripe
                │
          ┌─────┴────────────────────┐
          ▼                          ▼
    7a. Si paga:                7b. Si cancela:
    GET /bookings/success/      GET /home/?reserva_cancelada=1
          │
          ▼ (ReservaSuccessView)
    8. Verificar session con Stripe API
       session.payment_status == "paid"
          │
          ▼
    9. Reserva.estado = "confirmada"
       messages.success(...)
          │
          ▼
    10. GET /home/?reserva_ok=1
```

### El Webhook — La Doble Seguridad

```python
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        # Verificar que el mensaje viene REALMENTE de Stripe
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event['type'] == 'checkout.session.completed':
            ref = session.get('client_reference_id', '')
            
            # Distinguir si es una reserva o un producto
            if ref.startswith('reserva:'):
                reserva_id = int(ref.split('reserva:')[1])
                Reserva.objects.filter(pk=reserva_id).update(estado='confirmada')
            else:
                Pedido.objects.filter(id=ref).update(estado='completado', ...)
```

**`@csrf_exempt`**: Los webhooks de Stripe son peticiones POST que no vienen del navegador del usuario, sino de los servidores de Stripe. Django bloquearía estas peticiones porque no tienen token CSRF. Sin embargo, la seguridad se garantiza de otra forma: la verificación criptográfica de la firma (`STRIPE_WEBHOOK_SECRET`).

**`client_reference_id`**: Al crear la sesión de Stripe, se incluye un identificador personalizado que llega de vuelta en el evento del webhook. Con el prefijo `"reserva:"` se puede distinguir en un solo endpoint si el pago corresponde a una reserva de clase o a una compra de producto digital, evitando la necesidad de dos endpoints de webhook separados.

**`stripe.Webhook.construct_event()`**: Esta llamada verifica criptográficamente que el payload y la firma `HTTP_STRIPE_SIGNATURE` coinciden con el `STRIPE_WEBHOOK_SECRET`. Si alguien intenta enviar un webhook falso, esta verificación falla y la vista devuelve HTTP 400.

### La URL de Éxito con `{CHECKOUT_SESSION_ID}`

```python
base_url = request.build_absolute_uri(reverse("booking_success"))
success_url = f"{base_url}?reserva_id={reserva.pk}&session_id={{CHECKOUT_SESSION_ID}}"
```

El par de llaves `{{CHECKOUT_SESSION_ID}}` es un **placeholder especial de Stripe**: cuando Stripe redirige al usuario de vuelta, sustituye este texto por el ID real de la sesión de pago (ej. `cs_test_4eC39HqLyjWgluQW...`). Esto permite que `ReservaSuccessView` pueda llamar a `stripe.checkout.Session.retrieve(session_id)` para verificar el estado del pago directamente, sin necesidad de esperar al webhook.

---

## 14. El Sistema de Plantillas (Templates)

Las plantillas se organizan en la carpeta `templates/` y están divididas en subcarpetas que reflejan los contextos de la aplicación:

- **`portfolio/`**: Contiene las vistas principales: `landing.html`, `home.html`, `home_user.html`, `products.html`, `login.html`, `signup.html`, `dashboard_admin.html`, formularios de clases, etc.
- **`products/`**: Vistas del CRUD de administración de productos.
- **`users/`**: Perfil de usuario, listado de usuarios, formularios de gestión.
- **`account/`**: Plantillas de `django-allauth` para flujos de verificación de email, inactividad de cuenta, etc.
- **`socialaccount/`**: Plantillas de `django-allauth` para flujos OAuth (cancelación, errores de autenticación).

El uso de `crispy_forms` simplifica enormemente el renderizado de formularios. En lugar de escribir HTML manual para cada campo, se usa la etiqueta:

```html
{% load crispy_forms_tags %}
{{ form|crispy }}
```

Esto genera automáticamente los `div`, `label`, `input` y mensajes de error con las clases correctas de Bootstrap 5.

---

## 15. El Panel de Administración (Django Admin)

Django Admin está activo en `/admin/` y proporciona un CRUD completo de todos los modelos. Se ha personalizado con:

- **`ProductoAdmin`**: `list_editable = ("precio", "publicado")` permite editar precio y estado de publicación directamente desde el listado sin entrar al detalle.
- **`PedidoAdmin`** con `DetallePedidoInline`: Muestra las líneas del pedido integradas dentro de la vista del pedido.
- **`DescargaAdmin`**: Filtra por fecha y permite buscar descargas por email del usuario.

Para la configuración de OAuth de Google, el panel de Admin es donde se registra la `SocialApplication`:
1. `Sites > Social Applications > Añadir`
2. Proveedor: Google
3. Client ID: `(de Google Cloud Console)`
4. Secret key: `(de Google Cloud Console)`

---

## 16. Despliegue con Docker

### La Imagen de Producción (Dockerfile.prod)

```dockerfile
# Stage 1: Builder — instala las dependencias
FROM python:3.12-slim as builder
RUN apt-get install build-essential postgresql-client
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime — imagen final limpia y pequeña
FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local  # Solo los paquetes instalados
COPY . .
EXPOSE 8000
ENTRYPOINT ["/bin/sh", "/code/docker/entrypoint.sh"]
```

La imagen **multi-stage** es un patrón de optimización: `Stage 1` tiene todo lo necesario para compilar dependencias (como `build-essential` para paquetes con extensiones C), pero `Stage 2` solo copia los paquetes ya compilados. La imagen final no incluye el compilador, reduciéndose considerablemente.

### Los Servicios de Producción (docker-compose.prod.yml)

```yaml
services:
  postgres:                     # Base de datos
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]  # Comprueba si PostgreSQL está listo

  web:                          # Django + Gunicorn
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn FrameffX.wsgi:application --bind 0.0.0.0:8000 --workers 4"
    depends_on:
      postgres:
        condition: service_healthy  # No arranca hasta que PostgreSQL esté listo

  nginx:                        # Proxy inverso + SSL
    image: nginx:alpine
    volumes:
      - static_volume:/code/staticfiles:ro   # Sirve estáticos directamente
      - media_volume:/code/media:ro          # Sirve media directamente
      - ./certbot/conf:/etc/letsencrypt:ro   # Certificados SSL
```

**`depends_on: condition: service_healthy`**: Evita que Django intente conectarse a PostgreSQL antes de que el servidor de base de datos esté completamente listo. Sin este healthcheck, el contenedor `web` podría arrancar antes que `postgres` y fallar.

**Gunicorn con `--workers 4`**: Gunicorn crea 4 procesos worker en paralelo para servir peticiones concurrentes. La regla estándar es `(2 × núcleos_CPU) + 1` workers.

### El Script de Arranque (entrypoint.sh)

```bash
# Esperar a que PostgreSQL esté listo
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    sleep 1
done

# Migrar primero 'users' (otras apps dependen de ella por AUTH_USER_MODEL)
python manage.py migrate users --noinput
python manage.py migrate --noinput

# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Crear superusuario por defecto si no existe
python manage.py shell <<END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin@example.com', 'changeme')
END

# Arrancar Gunicorn
exec gunicorn FrameffX.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

El script migra `users` primero porque todas las demás apps tienen Foreign Keys a `AUTH_USER_MODEL`. Si se migraran en orden aleatorio, Django no encontraría la tabla de usuarios al crear las tablas de `bookings` o `products`.

---

## 17. Comandos de Gestión (Management Commands)

Se han creado comandos personalizados de Django (disponibles con `python manage.py`):

### `seed_products`

```python
class Command(BaseCommand):
    help = "Carga los productos del marketplace desde el fixture inicial."

    def handle(self, *args, **options):
        call_command("loaddata", "products/fixtures/initial_data.json", verbosity=0)
        total = Producto.objects.count()
        self.stdout.write(self.style.SUCCESS(f"[OK] {total} producto(s) disponibles en la BD."))
```

Encapsula la carga del fixture de productos con un nombre semántico. En lugar de recordar la ruta del fixture, el administrador ejecuta `python manage.py seed_products` y el sistema se encarga de encontrar y cargar el archivo JSON.

### `seed_teachings` (referenciado en documentación)

Similar a `seed_products`, carga las clases de demostración.

### `loaddata demo_data.json`

El fixture `demo_data.json` contiene un volcado completo de la base de datos en formato JSON: catálogo de clases, productos, usuarios de demostración y configuración. Permite reproducir el estado exacto de la plataforma en cualquier máquina con un solo comando.

---

## 18. Variables de Entorno y Seguridad

El archivo `.env` (que nunca se sube a Git gracias al `.gitignore`) centraliza todas las configuraciones sensibles:

```env
# Seguridad de Django
SECRET_KEY=django-insecure-...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (solo en producción con PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=frameffx_db
DB_USER=frameffx_user
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432

# Email (SMTP para producción)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Seguridad HTTPS (solo producción)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

En desarrollo local, `EMAIL_BACKEND=console.EmailBackend` hace que los emails no se envíen realmente sino que se impriman en la terminal, lo que facilita el debugging sin necesidad de un servidor SMTP real.

---

## 19. Flujo Completo de un Usuario

A continuación se describe el recorrido completo de un usuario nuevo en la plataforma:

### 1. Llegada y Registro
- El usuario visita `http://localhost:8000/` → `LandingView` (portfolio/landing.html).
- Hace clic en "Registrarse" → `SignupView` con `RegistroForm`.
- Introduce nombre, email y contraseña × 2. El formulario valida email único, seguridad de contraseña y coincidencia.
- Al enviar, `form.save()` crea el `Usuario` con contraseña encriptada en PBKDF2.
- `login()` lo autentica automáticamente → redirige a `home`.

### 2. Exploración del Catálogo de Clases
- El usuario ve `showTeachings` → solo clases con `estado="activa"` y `start_at` futuro.
- La paginación muestra 9 clases por página, ordenables por precio, fecha o recientes.
- El contexto incluye `reservas_ids` (set de clases ya reservadas) para que el template marque visualmente las clases ya reservadas.

### 3. Compra de un Preset en el Marketplace
- Navega a `/products/` → `showProducts` → solo productos `publicado=True`.
- Hace clic en "Comprar" → POST a `CreateCheckoutSessionView`.
- Django crea un `Pedido` (estado=`pendiente`) y un `DetallePedido` con el precio actual.
- Stripe Checkout redirige al usuario a la pasarela de pago.
- Tras pagar, Stripe redirige a `ProductSuccessView` con `?pedido_id=X&session_id=cs_...`.
- `session.payment_status == "paid"` → `Pedido.estado = "completado"`.
- El usuario puede descargar el archivo desde su perfil.

### 4. Descarga del Archivo Digital
- En el perfil o en la home ve sus compras.
- Hace clic en "Descargar" → `DownloadProductView`.
- Verificación: pedido completado + `Descarga.puede_descargar(detalle)`.
- Si pasa: se crea un registro `Descarga` (con IP) y Django sirve el archivo con `FileResponse`.
- Si superó el límite: mensaje de error.

### 5. Reserva de una Clase con Pago
- En la home del catálogo de clases, hace clic en "Reservar".
- POST a `ReservaCreateView` → 4 validaciones → crea `Reserva(estado="pendiente")`.
- Para pagar: POST a `ReservaCheckoutView` → crea sesión Stripe → redirige a pasarela.
- Tras pagar: `ReservaSuccessView` verifica con Stripe API → `Reserva.estado = "confirmada"`.

### 6. Vista del Administrador
- El admin visita `/dashboard-admin/` → `AdminDashboardView` (protegido por `StaffRequiredMixin`).
- Ve en tiempo real: total de usuarios, ingresos acumulados, últimos pedidos, reservas pendientes y próximas clases.
- Puede ir a `/admin/` para gestión completa, o a las URLs de CRUD de clases y productos.

---

*Documentación generada a partir del código fuente de FrameffX. Refleja el estado del proyecto a fecha de la última revisión.*
