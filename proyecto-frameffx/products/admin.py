# Inter_4 – Configuración del administrador de la app products
from django.contrib import admin

from .models import Descarga, DetallePedido, Pedido, Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "precio", "publicado", "archivo_digital")
    list_editable = ("precio", "publicado")
    search_fields = ("titulo", "descripcion")
    list_filter = ("tipo", "publicado")
    ordering = ("-fecha_creacion",)


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ("subtotal",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("pk", "usuario", "estado", "total", "fecha_creacion")
    list_filter = ("estado",)
    search_fields = ("usuario__email", "referencia_pago")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
    inlines = [DetallePedidoInline]


@admin.register(Descarga)
class DescargaAdmin(admin.ModelAdmin):
    list_display = ("detalle", "ip_origen", "fecha")
    list_filter = ("fecha",)
    search_fields = ("detalle__pedido__usuario__email",)
    readonly_fields = ("fecha",)

