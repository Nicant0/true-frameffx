# Inter_5 – Introducción de datos de prueba usando Faker
from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import timedelta

from teachings.models import Teaching


class Command(BaseCommand):
    help = "Genera datos de prueba para el modelo Teaching"

    def handle(self, *args, **options):
        fake = Faker("es_ES")
        total = 500

        self.stdout.write(
            self.style.WARNING(f"Creando {total} clases de prueba...")
        )

        for _ in range(total):
            inicio = fake.date_time_between(start_date="+1d", end_date="+6M")
            duracion = random.choice([60, 90, 120, 180])
            fin = inicio + timedelta(minutes=duracion)

            Teaching.objects.create(
                title=fake.sentence(nb_words=4),
                description=fake.paragraph(nb_sentences=5),
                price=round(random.uniform(15, 150), 2),
                start_at=inicio,
                end_at=fin,
                duracion_min=duracion,
                estado=random.choice(
                    ["activa", "cancelada", "finalizada"]
                ),
            )

        self.stdout.write(
            self.style.SUCCESS("✔ 500 clases creadas correctamente")
        )
