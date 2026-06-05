from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    """Formulario para crear y editar productos del Marketplace."""

    class Meta:
        model = Producto
        fields = [
            "titulo",
            "descripcion",
            "tipo",
            "precio",
            "publicado",
            "archivo_digital",
            "imagen_portada",
            "max_descargas",
        ]
