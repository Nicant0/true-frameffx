# Inter_4 – Configuración del administrador de la app teachings
from django.contrib import admin
from .models import Teaching


@admin.register(Teaching)
class TeachingAdmin(admin.ModelAdmin):
    # Inter_4.a – Campos que se muestran en el listado del administrador
    list_display = ("title", "start_at", "end_at", "price", "estado", "duracion_min")

    # Inter_4.a – Campos por los que se puede buscar
    search_fields = ("title", "description")

    # Inter_4.a – Filtros laterales del administrador
    list_filter = ("estado", "start_at")

    # Inter_4.a – Ordenación por defecto
    ordering = ("start_at",)
