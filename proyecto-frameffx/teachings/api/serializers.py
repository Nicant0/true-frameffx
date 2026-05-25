from rest_framework import serializers
from teachings.models import Teaching

class TeachingSerializer(serializers.ModelSerializer):
    class Meta:  # pyrefly: ignore[bad-override]
        model = Teaching
        fields = [
            'id',
            'title',
            'price',
            'duracion_min',
            'estado',
            'description',
            'start_at',
            'end_at',
            'fecha_creacion',
        ]