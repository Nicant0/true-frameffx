from django.db import models
from django.conf import settings

class Reserva(models.Model):
    """
    Representa la solicitud y asignación de un usuario a una clase virtual.

    He añadido la restricción `unique_together` al final de este modelo para garantizar 
    a nivel de base de datos que un usuario no pueda reservar la misma clase más de una vez.
    
    Flujo de estados:
    - Empieza en 'pendiente_pago' al pulsar "Reservar".
    - Pasa a 'confirmada' cuando Stripe envía el webhook de éxito.
    """

    ESTADO_RESERVA_CHOICES = [
        ("pendiente_pago", "Pendiente de pago"),
        ("pendiente",     "Pendiente"),
        ("confirmada",    "Confirmada"),
        ("cancelada",     "Cancelada"),
        ("caducada",      "Caducada"),
    ]

    clase = models.ForeignKey(
        "teachings.Teaching", 
        on_delete=models.PROTECT,
        related_name="reservas",
        verbose_name="Clase"
    )      


    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservas",
        verbose_name="Usuario",
    )   

    fecha_reserva = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de la reserva"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_RESERVA_CHOICES,
        default="pendiente",
        verbose_name="Estado de la reserva"
    )

    caducidad = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de caducidad"
    )

    nota = models.TextField(
        blank=True,
        verbose_name="Nota"
    )

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        db_table = "reservas"
        unique_together = ("clase", "usuario")

    def __str__(self):
        return f"Reserva #{self.id} - {self.usuario} - {self.clase}"
