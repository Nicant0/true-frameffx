from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario. He creado esto porque en mi proyecto
    el identificador primario para el registro y login será el 'email' en lugar del
    tradicional 'username' que trae Django por defecto.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un email")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True')

        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de Usuario personalizado (Custom User Model) para FrameffX.

    He reemplazado la implementación estándar de Django para obligar a usar el 'email'
    como credencial de acceso principal (USERNAME_FIELD). Sigo manteniendo los roles
    y permisos estándar (is_staff, is_superuser, is_active) y dejo el campo 'username'
    como secundario y opcional, pensado para mostrar un apodo en la interfaz sin
    complicar el login.
    """

    username = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    email = models.EmailField(
        unique=True
    )

    # Campos de Perfil de Usuario
    foto_perfil = models.ImageField(
        upload_to='perfiles/',
        null=True,
        blank=True
    )
    biografia = models.TextField(
        max_length=500,
        null=True,
        blank=True
    )
    telefono = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    activo = models.BooleanField(default=True)

    create_date = models.DateTimeField(
        auto_now_add=True
    )

    update_date = models.DateTimeField(
        auto_now=True
    )

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    # Manager personalizado
    objects = UsuarioManager()

    # Campo identificador
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
