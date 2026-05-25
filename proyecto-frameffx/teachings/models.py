from django.db import models


class Teaching(models.Model):
    """
    Representa una clase virtual, curso o mentoría que ofrezco en la plataforma.

    He diseñado este modelo almacenando explícitamente tanto `start_at` y `end_at` 
    como `duracion_min`. Aunque la duración se puede calcular al vuelo, he preferido 
    guardarla precalculada para simplificar las consultas a la base de datos y 
    mejorar el rendimiento a la hora de renderizar las cards del catálogo.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    duracion_min = models.PositiveIntegerField()

    ESTADOS = [
        ("activa", "Activa"),
        ("cancelada", "Cancelada"),
        ("finalizada", "Finalizada"),
    ]

    estado = models.CharField(max_length=20, choices=ESTADOS, default="activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_at"]
        unique_together = ("title", "start_at")

    def __str__(self):
        return self.title