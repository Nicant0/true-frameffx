import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FrameffX.settings")
django.setup()

from teachings.models import Teaching

def main():
    print("Testing dynamic states...")
    now = timezone.now()
    t = Teaching(
        title="Clase Caducada",
        description="test",
        price=10,
        start_at=now - timedelta(days=2),
        end_at=now - timedelta(days=2, hours=-1),
        duracion_min=60,
        estado="activa"
    )
    t.save()
    
    print(f"Is active now? {t.is_active_now}")
    print(f"Is finished now? {t.is_finished_now}")

    # clean up
    t.delete()

if __name__ == "__main__":
    main()
