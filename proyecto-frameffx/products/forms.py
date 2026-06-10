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

    def clean_imagen_portada(self):
        foto = self.cleaned_data.get('imagen_portada')
        if foto:
            # Límite de 5 MB para evitar cargar portadas enormes que ralenticen la web
            if foto.size > 5 * 1024 * 1024:
                from django.core.exceptions import ValidationError
                raise ValidationError("La imagen de portada no puede pesar más de 5MB. Por favor, optimízala.")
        return foto
