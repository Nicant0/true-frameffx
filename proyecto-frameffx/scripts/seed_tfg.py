"""
seed_tfg.py – Script de generación de datos de prueba para la defensa del TFG FrameFFX

Uso (desde el directorio raíz del proyecto, con el .venv activado):
    python scripts/seed_tfg.py

Crea automáticamente:
  · Un superusuario admin  (admin@frameffx.com / Admin1234!)
  · Un usuario normal demo (demo@frameffx.com  / Demo1234!)
  · 5 Productos digitales con datos realistas
  · 5 Clases virtuales (Teaching) en diferentes estados
  · 2 Reservas para el usuario demo
  · 1 Pedido completado para el usuario demo (para demostrar la descarga)

Idempotente: si los datos ya existen, los omite sin error.
"""

import os
import sys
import django
from datetime import timedelta
from decimal import Decimal

# Configuración de Django: añade el directorio del proyecto al path de Python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FrameffX.settings")
django.setup()

# Imports de modelos (deben ir después de django.setup())
from django.utils import timezone
from django.db import transaction

from users.models import Usuario
from products.models import Producto, Pedido, DetallePedido
from teachings.models import Teaching
from bookings.models import Reserva


# Funciones auxiliares de creación de datos

def crear_usuario(email, password, is_staff=False, is_superuser=False):
    if Usuario.objects.filter(email=email).exists():
        print(f"  [SKIP] Usuario ya existe: {email}")
        return Usuario.objects.get(email=email)
    user = Usuario.objects.create_user(
        email=email,
        password=password,
        is_staff=is_staff,
        is_superuser=is_superuser,
        is_active=True,
    )
    print(f"  [OK]   Usuario creado: {email}")
    return user


def crear_producto(titulo, tipo, precio, descripcion, max_descargas=3):
    obj, created = Producto.objects.get_or_create(
        titulo=titulo,
        tipo=tipo,
        defaults={
            "precio": Decimal(precio),
            "descripcion": descripcion,
            "publicado": True,
            "max_descargas": max_descargas,
        }
    )
    if created:
        print(f"  [OK]   Producto creado: {titulo}")
    else:
        print(f"  [SKIP] Producto ya existe: {titulo}")
    return obj


def crear_clase(titulo, descripcion, precio, duracion, inicio_offset_days, estado="activa"):
    start_at = timezone.now() + timedelta(days=inicio_offset_days)
    end_at = start_at + timedelta(minutes=duracion)

    obj, created = Teaching.objects.get_or_create(
        title=titulo,
        defaults={
            "description": descripcion,
            "price": Decimal(precio),
            "duracion_min": duracion,
            "start_at": start_at,
            "end_at": end_at,
            "estado": estado,
        }
    )
    if created:
        print(f"  [OK]   Clase creada: {titulo} ({estado})")
    else:
        print(f"  [SKIP] Clase ya existe: {titulo}")
    return obj


# Función principal del script

def main():
    print("\n" + "="*60)
    print("  FrameFFX — Generador de Datos TFG")
    print("="*60)

    # 1. Usuarios
    print("\n[1/4] Creando usuarios...")
    admin = crear_usuario(
        email="admin@frameffx.com",
        password="Admin1234!",
        is_staff=True,
        is_superuser=True,
    )
    demo = crear_usuario(
        email="demo@frameffx.com",
        password="Demo1234!",
    )

    # 2. Productos
    print("\n[2/4] Creando productos digitales...")
    p1 = crear_producto(
        titulo="Cinematic LUT Pack Vol. 1",
        tipo="preset",
        precio="29.99",
        descripcion=(
            "Pack de 15 LUTs cinematográficos listos para DaVinci Resolve y Premiere Pro. "
            "Consigue ese look de película de Hollywood en segundos. Compatibles con footage "
            "LOG de Sony, Canon, Blackmagic y Fujifilm."
        ),
        max_descargas=3,
    )
    p2 = crear_producto(
        titulo="Guía de Colorización Profesional",
        tipo="guia",
        precio="19.99",
        descripcion=(
            "Guía completa en PDF (85 páginas) sobre flujos de trabajo de colorización "
            "para cine y publicidad. Incluye teoría del color, uso de nodos en DaVinci "
            "y técnicas avanzadas de matching."
        ),
        max_descargas=5,
    )
    p3 = crear_producto(
        titulo="Motion Graphics Essentials",
        tipo="bundle",
        precio="49.99",
        descripcion=(
            "Bundle con 30 plantillas de After Effects para títulos, transiciones y "
            "elementos de UI. Totalmente customizables. Ideales para YouTube, publicidad "
            "y proyectos corporativos."
        ),
        max_descargas=3,
    )
    p4 = crear_producto(
        titulo="Plugin de Noise Reduction",
        tipo="plugin",
        precio="39.99",
        descripcion=(
            "Plugin VST/AU para eliminación de ruido en pistas de audio. "
            "Basado en algoritmos de IA, reduce el ruido de fondo hasta un 95% "
            "manteniendo la naturalidad de la voz."
        ),
        max_descargas=2,
    )
    p5 = crear_producto(
        titulo="Proyecto DaVinci Resolve — Wedding Cinematic",
        tipo="proyecto",
        precio="34.99",
        descripcion=(
            "Proyecto completo de DaVinci Resolve para edición de bodas cinemáticas. "
            "Incluye color grading, títulos, transiciones y timeline pre-montado. "
            "Solo importa tu metraje y personaliza."
        ),
        max_descargas=3,
    )

    # 3. Clases virtuales
    print("\n[3/4] Creando clases virtuales...")
    c1 = crear_clase(
        titulo="Introducción a DaVinci Resolve",
        descripcion=(
            "Aprende los fundamentos de DaVinci Resolve desde cero. Exploraremos la "
            "interfaz, el flujo de trabajo básico de edición y las primeras técnicas "
            "de color grading. Perfecta para principiantes."
        ),
        precio="59.99",
        duracion=90,
        inicio_offset_days=3,
        estado="activa",
    )
    c2 = crear_clase(
        titulo="Color Grading Avanzado con Nodos",
        descripcion=(
            "Domina el sistema de nodos de DaVinci Resolve para crear looks "
            "cinemáticos complejos. Aprenderás técnicas de power windows, "
            "qualifiers y tracking de color."
        ),
        precio="79.99",
        duracion=120,
        inicio_offset_days=7,
        estado="activa",
    )
    c3 = crear_clase(
        titulo="Edición de Vídeo con Premiere Pro",
        descripcion=(
            "Sesión enfocada en las mejores prácticas de edición con Adobe Premiere Pro. "
            "Multicámara, efectos de sonido, exportación y optimización para redes sociales."
        ),
        precio="49.99",
        duracion=60,
        inicio_offset_days=14,
        estado="activa",
    )
    c4 = crear_clase(
        titulo="After Effects: Motion Graphics desde Cero",
        descripcion=(
            "Diseña animaciones e infografías animadas en After Effects. "
            "Aprende keyframes, expresiones básicas y la creación de plantillas "
            "reutilizables para tus proyectos."
        ),
        precio="69.99",
        duracion=90,
        inicio_offset_days=21,
        estado="activa",
    )
    c5 = crear_clase(
        titulo="Fundamentos de Cinematografía",
        descripcion=(
            "Clase especial sobre composición visual, movimientos de cámara y uso "
            "de la luz natural. Ideal para camarógrafos y directores que quieren "
            "elevar la calidad estética de sus producciones."
        ),
        precio="89.99",
        duracion=120,
        inicio_offset_days=-5,  # pasada, para mostrar "finalizada"
        estado="finalizada",
    )

    # 4. Reservas y pedidos para el usuario demo
    print("\n[4/4] Creando reservas y pedido de demo...")

    # Reserva activa para demo
    reserva1, cr1 = Reserva.objects.get_or_create(
        clase=c1, usuario=demo,
        defaults={"estado": "confirmada"}
    )
    print(f"  {'[OK]  ' if cr1 else '[SKIP]'} Reserva: {demo.email} -> {c1.title}")

    # Reserva pendiente
    reserva2, cr2 = Reserva.objects.get_or_create(
        clase=c3, usuario=demo,
        defaults={"estado": "pendiente"}
    )
    print(f"  {'[OK]  ' if cr2 else '[SKIP]'} Reserva: {demo.email} -> {c3.title}")

    # Pedido completado para que el usuario pueda "descargar"
    if not Pedido.objects.filter(usuario=demo, estado="completado").exists():
        pedido = Pedido.objects.create(
            usuario=demo,
            estado="completado",
            total=p1.precio,
            referencia_pago="pi_demo_test_frameffx_tfg",
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=p1,
            precio_unitario=p1.precio,
            cantidad=1,
        )
        print(f"  [OK]   Pedido completado creado para {demo.email}: {p1.titulo}")
    else:
        print(f"  [SKIP] Pedido completado ya existe para {demo.email}")

    # Resumen final
    print("\n" + "="*60)
    print("  ¡Datos generados con exito!")
    print("="*60)
    print(f"\n  [ADMIN]  admin@frameffx.com  /  Admin1234!")
    print(f"  [DEMO]   demo@frameffx.com   /  Demo1234!")
    print(f"\n  Productos:  {Producto.objects.count()}")
    print(f"  Clases:     {Teaching.objects.count()}")
    print(f"  Reservas:   {Reserva.objects.count()}")
    print(f"  Pedidos:    {Pedido.objects.count()}")
    print("\n  Ejecuta el servidor con:")
    print("  python manage.py runserver\n")


if __name__ == "__main__":
    with transaction.atomic():  # type: ignore[attr-defined]
        main()
