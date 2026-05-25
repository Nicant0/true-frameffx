# Inter_4.d – Configuración de la app teachings
from django.apps import AppConfig


class TeachingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'teachings'
    verbose_name = "Gestión de clases"
