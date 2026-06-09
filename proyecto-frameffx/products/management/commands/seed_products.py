"""
Comando de gestión: seed_products
──────────────────────────────────
Carga el fixture inicial de productos del marketplace.
Uso:
    python manage.py seed_products
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from products.models import Producto


class Command(BaseCommand):
    help = "Carga los productos del marketplace desde el fixture inicial (products/fixtures/initial_data.json)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("[*] Cargando productos del marketplace..."))
        try:
            call_command("loaddata", "products/fixtures/initial_data.json", verbosity=0)
            total = Producto.objects.count()
            self.stdout.write(self.style.SUCCESS(f"[OK] {total} producto(s) disponibles en la BD."))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"[ERROR] Al cargar el fixture: {exc}"))
