from rest_framework import serializers
from products.models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:  # pyrefly: ignore[bad-override]
        model = Producto
        fields = [
            'id',
            'titulo',
            'descripcion',
            'tipo',
            'precio',
            'publicado',
            'imagen_portada',
            'max_descargas',
            'fecha_creacion',
        ]