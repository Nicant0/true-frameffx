"""
bookings/checkout_views.py
Gestiona el flujo de pago Stripe para la reserva de clases virtuales.

He programado el siguiente flujo de vida de la reserva:
  1. El usuario hace POST a ReservaCheckoutView (desde el modal).
  2. Compruebo que la clase esté activa y que el usuario no la tenga ya reservada.
  3. Creo un registro en la BD con estado='pendiente_pago'.
  4. Levanto una sesión de Stripe Checkout y redirijo al usuario allí.
  5. Si el pago es exitoso, el webhook asíncrono actualiza la Reserva a 'confirmada'.
"""

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError, IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View

from teachings.models import Teaching
from .models import Reserva

stripe.api_key = settings.STRIPE_SECRET_KEY


class ReservaCheckoutView(LoginRequiredMixin, View):
    """
    Controlador para iniciar el pago Stripe al reservar una clase.

    Para proteger la integridad de los datos, realizo tres validaciones previas:
      1. Evito que los administradores puedan reservar clases accidentalmente.
      2. Verifico que la clase siga estando 'activa'.
      3. Consulto la BD para evitar duplicados si el usuario ya tiene una reserva activa.

    Si todo es correcto, creo la Reserva ('pendiente_pago') y redirijo a Stripe.
    """

    http_method_names = ["post"]

    def post(self, request, pk, *args, **kwargs):
        # ── 1. Admins no reservan ───────────────────────────────────────────
        if request.user.is_staff:
            messages.error(request, "Los administradores no pueden realizar reservas.")
            return redirect("home")

        # ── 2. La clase existe y está activa ───────────────────────────────
        clase = get_object_or_404(Teaching, pk=pk)
        if not clase.is_active_now:
            messages.warning(
                request,
                f"La clase «{clase.title}» ya no está disponible para reservar "
                f"(estado o fecha finalizados).",
            )
            return redirect("home")

        # ── 3. No duplicar reserva activa ───────────────────────────────────
        reserva_existente = Reserva.objects.filter(
            clase=clase,
            usuario=request.user,
        ).exclude(estado__in=["cancelada", "caducada"]).first()

        if reserva_existente:
            if reserva_existente.estado == "confirmada":
                messages.info(
                    request,
                    f"Ya tienes una reserva confirmada para «{clase.title}».",
                )
            elif reserva_existente.estado == "pendiente_pago":
                messages.warning(
                    request,
                    f"Ya tienes un pago pendiente para «{clase.title}». "
                    "Completa el pago o cancela la reserva antes de intentarlo de nuevo.",
                )
            else:
                messages.info(
                    request,
                    f"Ya tienes una reserva activa para «{clase.title}» "
                    f"(estado: {reserva_existente.get_estado_display()}).",
                )
            return redirect("home")

        # ── 4. Crear reserva en estado 'pendiente_pago' ────────────────────
        try:
            reserva = Reserva.objects.create(
                clase=clase,
                usuario=request.user,
                estado="pendiente_pago",
            )
        except IntegrityError:
            messages.error(
                request,
                "Ya existe una reserva para esta clase. "
                "Puede que la hayas creado en otra pestaña.",
            )
            return redirect("home")
        except DatabaseError:
            messages.error(request, "Error interno de base de datos. Inténtalo de nuevo.")
            return redirect("home")

        # ── 5. Crear sesión de Stripe ──────────────────────────────────────
        domain_url = request.build_absolute_uri("/")[:-1]

        try:
            # Prefijamos con "reserva:" para que el webhook sepa que es una clase
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=f"reserva:{reserva.pk}",
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "eur",
                            "unit_amount": int(clase.price * 100),
                            "product_data": {
                                "name": f"Clase: {clase.title}",
                                "description": (
                                    f"Duración: {clase.duracion_min} min · "
                                    f"Inicio: {clase.start_at.strftime('%d/%m/%Y %H:%M')}"
                                ),
                            },
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=(
                    domain_url
                    + reverse("home")
                    + "?reserva_ok=1&clase="
                    + str(clase.pk)
                ),
                cancel_url=(
                    domain_url
                    + reverse("home")
                    + "?reserva_cancelada=1"
                ),
            )
            return redirect(checkout_session.url, code=303)

        except Exception as e:
            # Si Stripe falla, eliminamos la reserva para no dejar datos huérfanos
            reserva.delete()
            messages.error(
                request,
                f"No se pudo iniciar el pago: {e}. Inténtalo de nuevo más tarde.",
            )
            return redirect("home")
