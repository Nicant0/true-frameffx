"""
Comando de gestión: seed_teachings
────────────────────────────────────
Carga el fixture inicial de clases virtuales (teachings).
Uso:
    python manage.py seed_teachings
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from teachings.models import Teaching


class Command(BaseCommand):
    help = "Carga las clases virtuales desde el fixture inicial (teachings/fixtures/initial_data.json)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("[*] Cargando clases virtuales..."))
        try:
            call_command("loaddata", "teachings/fixtures/initial_data.json", verbosity=0)
            total = Teaching.objects.count()
            self.stdout.write(self.style.SUCCESS(f"[OK] {total} clase(s) disponibles en la BD."))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"[ERROR] Al cargar el fixture: {exc}"))
