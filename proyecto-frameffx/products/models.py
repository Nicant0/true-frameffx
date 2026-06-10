from django.conf import settings
from django.db import models


class Producto(models.Model):
    """
    Representa un artículo digital en el marketplace (presets, guías, bundles).
    Diseñado para ser flexible y soportar distintos tipos de archivos,
    con un límite de descargas por comprador para mayor control.
    """

    # Tipos posibles de producto
    TIPOS_PRODUCTO = [
        ("preset", "Preset"),
        ("guia", "Guía"),
        ("plugin", "Plugin"),
        ("proyecto", "Archivo de proyecto"),
        ("bundle", "Bundle"),
    ]

    # Campos principales
    titulo = models.CharField(
        max_length=150,
        verbose_name="Título"
    )
    descripcion = models.TextField(
        verbose_name="Descripción"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_PRODUCTO,
        verbose_name="Tipo de producto"
    )
    precio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Precio"
    )
    publicado = models.BooleanField(
        default=True,
        verbose_name="Publicado"
    )

    # Recurso digital y archivos asociados
    archivo_digital = models.FileField(
        upload_to="productos/archivos/",
        null=True,
        blank=True,
        verbose_name="Archivo digital",
        help_text="Archivo que el usuario descargará tras la compra (ZIP, LUT, etc.)"
    )
    imagen_portada = models.ImageField(
        upload_to="productos/portadas/",
        null=True,
        blank=True,
        verbose_name="Imagen de portada"
    )
    max_descargas = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="Descargas permitidas",
        help_text="Número máximo de veces que el comprador puede descargar el archivo"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["-fecha_creacion"]
        unique_together = ("titulo", "tipo")


# Modelos transaccionales de la tienda

class Pedido(models.Model):
    """
    Representa la cabecera de una compra realizada por un usuario.
    El pedido se divide en cabecera (Pedido) y líneas de detalle (DetallePedido)
    siguiendo las buenas prácticas de normalización de bases de datos.
    """

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente de pago"),
        ("completado", "Completado"),
        ("reembolsado", "Reembolsado"),
        ("cancelado", "Cancelado"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos",
        verbose_name="Usuario",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="pendiente",
        verbose_name="Estado del pedido",
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total",
    )
    # Referencia externa de pasarela de pago (ej. Stripe PaymentIntent ID)
    referencia_pago = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Referencia de pago",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"Pedido #{self.pk} – {self.usuario} ({self.estado})"


class DetallePedido(models.Model):
    """
    Línea de detalle que vincula un Producto a un Pedido.
    Almacena el 'precio_unitario' histórico para que futuros cambios de precio
    en el producto no alteren el total de los pedidos ya completados.
    """

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="Pedido",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,   # El producto no puede eliminarse si tiene pedidos asociados
        related_name="detalles_pedido",
        verbose_name="Producto",
    )
    # El precio se guarda en el momento de la compra para preservar el registro contable
    # aunque el precio del producto se modifique en el futuro
    precio_unitario = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Precio unitario (histórico)",
    )
    cantidad = models.PositiveSmallIntegerField(default=1, verbose_name="Cantidad")

    class Meta:
        verbose_name = "Línea de pedido"
        verbose_name_plural = "Líneas de pedido"
        unique_together = ("pedido", "producto")

    def subtotal(self):
        return self.precio_unitario * self.cantidad  # type: ignore

    def __str__(self):
        return f"{self.cantidad}× {self.producto} (Pedido #{self.pedido_id})"


class Descarga(models.Model):
    """
    Registra cada descarga efectiva de un archivo digital por parte de un usuario.
    Permite controlar el número de veces que un comprador descarga el archivo,
    haciendo respetar el límite definido en el campo max_descargas del Producto.
    """

    detalle = models.ForeignKey(
        DetallePedido,
        on_delete=models.CASCADE,
        related_name="descargas",
        verbose_name="Línea de pedido",
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de descarga")
    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP de origen",
    )

    class Meta:
        verbose_name = "Descarga"
        verbose_name_plural = "Descargas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Descarga de '{self.detalle.producto}' por {self.detalle.pedido.usuario} ({self.fecha:%Y-%m-%d %H:%M})"

    @classmethod
    def puede_descargar(cls, detalle: DetallePedido) -> bool:
        """Devuelve True si el usuario todavía tiene descargas disponibles."""
        usadas = cls.objects.filter(detalle=detalle).count()
        return usadas < detalle.producto.max_descargas
