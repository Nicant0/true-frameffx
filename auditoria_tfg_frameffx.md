# Auditoría de Arquitectura y Seguridad - FrameFFX (Django)

He realizado un análisis exhaustivo del espacio de trabajo de **FrameFFX**. A continuación, presento el informe de auditoría detallado estructurado según tus requerimientos.

## 1. ¿QUÉ TENGO HECHO ACTUALMENTE?
A nivel estructural, el proyecto tiene una base sólida configurada en Django 5.2 con la siguiente arquitectura de aplicaciones:

*   **`users`**: Implementa un modelo `Usuario` personalizado que extiende `AbstractBaseUser`, utilizando el correo electrónico como identificador (`USERNAME_FIELD`). Posee vistas CRUD protegidas y Mixins básicos.
*   **`products`**: Dispone de un modelo básico `Producto` (preset, guía, plugin, etc.) y una vista pública (`showProducts`) que simplemente renderiza un template.
*   **`teachings`**: Contiene la lógica principal de las clases virtuales. Tienes un modelo `Teaching` muy completo, junto a vistas para listar, filtrar, crear, editar y eliminar clases.
*   **`bookings`**: Existe el modelo `Reserva` que asocia eficientemente a los usuarios con las clases.
*   **Configuraciones generales**: Rutas definidas para APIs (`djoser`, `rest_framework`, `simplejwt`), autenticación con `allauth`, y configuraciones de seguridad para paso a producción preparadas en `settings.py`.

> [!NOTE]
> La arquitectura en sub-aplicaciones es limpia y escalable. Sin embargo, hay áreas críticas incompletas relacionadas con la lógica de negocio central de la tienda.

---

## 2. DIAGNÓSTICO DE LA BASE DE DATOS (models.py)
Las relaciones actuales (como la de `Reserva` vinculando `Usuario` y `Teaching` mediante `ForeignKey` y `unique_together`) son correctas y eficientes para el calendario. Sin embargo, para la "tienda online", **existen fallos graves por omisión**:

*   **Faltan los archivos descargables:** El modelo `Producto` (`products/models.py`) define título y precio, pero no tiene ningún `FileField` o `URLField` para almacenar el recurso digital que el cliente va a comprar (el preset, el proyecto, etc.).
*   **Faltan los modelos de Pedidos y Descargas:** No hay trazabilidad transaccional. Necesitas un modelo `Pedido` (vinculado a `Usuario`) y un `DetallePedido` (vinculado a `Pedido` y a `Producto`). Del mismo modo, para controlar los accesos, deberías tener un modelo `Descarga` que limite cuántas veces un usuario puede bajarse el archivo tras comprarlo.

---

## 3. DIAGNÓSTICO DE SEGURIDAD Y ROLES (views.py / settings.py)

### Roles (Administrador, Usuario, Invitado)
*   **Invitados Bloqueados en Clases:** El prompt indica que los invitados deben poder interactuar (probablemente ver el catálogo). Sin embargo, en `teachings/views.py`, la vista `showTeachings` (el Home) utiliza `LoginRequiredMixin`. Esto significa que si un invitado no está logueado, es expulsado de la página principal automáticamente.
*   **Mixins redundantes:** Tienes un `PublicAccessMixin` en `users/mixins.py` que hereda de `AccessMixin` pero no hace nada útil. Si una vista es pública, basta con usar `TemplateView` o `ListView` estándar.

### Google OAuth (Autenticación)
> [!WARNING]
> La configuración de Google OAuth **no está completada y fallará**.

*   Tienes instalados `allauth.account` y `allauth.socialaccount`, pero en `INSTALLED_APPS` (en `settings.py`) **te falta añadir el proveedor:** `'allauth.socialaccount.providers.google'`.
*   Tampoco existe la configuración `SOCIALACCOUNT_PROVIDERS` en tu `settings.py` (que es donde se definen los scopes y parámetros de la API de Google).

---

## 4. ERRORES CRÍTICOS Y MEJORAS DE CÓDIGO

*   **Antipatrón en `teachings/views.py` (Error Crítico de Diseño):**
    En la vista `showTeachings` (que es una `ListView`), has inyectado un método `post()` para manejar la creación de las reservas.
    ```python
    def post(self, request, *args, **kwargs):
        # Lógica de creación de reserva...
    ```
    *Mejora:* Crear una reserva no es responsabilidad de la vista que "lista las clases". Esto viola el Principio de Responsabilidad Única. Debes mover esta lógica a una vista dedicada dentro de la app `bookings` (ej: `ReservaCreateView` o un endpoint API).
*   **Rutas Hardcodeadas:** En `settings.py`, usas `LOGIN_REDIRECT_URL = '/home/'`. Es mejor práctica usar el nombre de la ruta: `LOGIN_REDIRECT_URL = 'home'`.
*   **Validaciones Faltantes en Reservas:** Actualmente tu código permite que un usuario intente reservar clases con estado "cancelada" o "finalizada" si manipula el `clase_id` del formulario, ya que el método POST no valida exhaustivamente el estado temporal, solo pide que sea `activa`.

---

## 5. APARTADO VISUAL (CSS/HTML)
Actualmente el proyecto está configurado para usar `crispy_bootstrap5`. Si bien Bootstrap es funcional, no transmite la sensación "premium y oscura" habitual en la industria del *filmmaking* y la edición de vídeo.

> [!TIP]
> **Recomendación: Migrar a Tailwind CSS.**
> Para un TFG que busca destacar visualmente, Tailwind ofrece muchísima más flexibilidad para lograr estéticas modernas (glassmorphism, gradientes, dark mode nativo).
>
> 1. Instala `django-tailwind`.
> 2. Implementa un **Dark Mode** como predeterminado (fondos `bg-zinc-950` o `bg-neutral-900`).
> 3. Usa colores de acento vibrantes pero sutiles para los botones (ej. un `cyan-500` o `violet-600` para evocar luces de neón o software de edición).
> 4. Usa fuentes modernas de Google Fonts como *Inter* o *Outfit*.

---

## 6. HOJA DE RUTA PRIORIZADA (TO-DO LIST)

Aquí tienes los pasos exactos y ordenados que debes seguir para completar el TFG:

1.  **Fase 1: Corrección de Base de Datos (E-commerce Core)**
    *   Añadir un campo `archivo_digital = models.FileField(...)` al modelo `Producto`.
    *   Crear el modelo `Pedido` en una nueva app (o dentro de products/bookings) vinculado a `Usuario`.
    *   Crear modelo `DetallePedido` para vincular los productos comprados.
2.  **Fase 2: Refactorización de Vistas y Permisos**
    *   Mover el método `post` de reservas desde `teachings/views.py` hacia una vista propia en `bookings`.
    *   Quitar el `LoginRequiredMixin` del Home (`showTeachings`) para que los invitados puedan ver las clases. Controlar en el template (HTML) que el botón "Reservar" te redirija al Login si eres invitado.
3.  **Fase 3: Reparación de Autenticación Google**
    *   Añadir el provider de Google a `INSTALLED_APPS`.
    *   Configurar `SOCIALACCOUNT_PROVIDERS` en `settings.py`.
    *   Crear credenciales de OAuth 2.0 en Google Cloud Console e insertarlas en la base de datos de Django (mediante el panel de Admin).
4.  **Fase 4: Rediseño Visual (Tailwind)**
    *   Instalar `django-tailwind` y purgar Bootstrap.
    *   Diseñar las plantillas con un esquema oscuro y aplicar componentes UI dinámicos.
5.  **Fase 5: Pasarela de Pago (Checkout)**
    *   Implementar **Stripe** para procesar los pagos de los productos y generar las descargas seguras.
