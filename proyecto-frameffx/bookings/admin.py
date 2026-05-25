from django.contrib import admin
from .models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'clase', 'get_clase_fecha', 'get_clase_hora', 'estado')
    list_filter = ('estado', 'clase__start_at')
    search_fields = ('usuario__email', 'usuario__username', 'clase__title')
    autocomplete_fields = ('usuario', 'clase')
    ordering = ('-fecha_reserva',)

    @admin.display(description='Fecha de la clase', ordering='clase__start_at')
    def get_clase_fecha(self, obj):
        return obj.clase.start_at.date() if obj.clase and obj.clase.start_at else None

    @admin.display(description='Hora de inicio')
    def get_clase_hora(self, obj):
        return obj.clase.start_at.time() if obj.clase and obj.clase.start_at else None
