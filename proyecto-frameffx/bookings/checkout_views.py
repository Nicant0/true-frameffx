"""
bookings/checkout_views.py
Gestiona el flujo de pago Stripe para la reserva de clases virtuales.

He programado el siguiente flujo de vida de la reserva:
  1. El usuario hace POST a ReservaCheckoutView (desde el modal).
  2. Compruebo que la clase esté activa y que el usuario no la tenga ya reservada.
  3. Creo un registro en la BD con estado='pendiente_pago'.
  4. Levanto una sesión de Stripe Checkout y redirijo al usuario allí.
  5a. (Producción) El webhook asíncrono actualiza la Reserva a 'confirmada'.
  5b. (Desarrollo/Demo) ReservaSuccessView verifica la sesión directamente con la API
      de Stripe y confirma la reserva — no requiere webhook local.
"""

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError, IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
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

        reserva = None

        if reserva_existente:
            if reserva_existente.estado == "confirmada":
                messages.info(
                    request,
                    f"Ya tienes una reserva confirmada para «{clase.title}».",
                )
                return redirect("home")
            elif reserva_existente.estado == "pendiente_pago":
                # En lugar de bloquear, REUTILIZAMOS la reserva pendiente
                reserva = reserva_existente
            else:
                messages.info(
                    request,
                    f"Ya tienes una reserva activa para «{clase.title}» "
                    f"(estado: {reserva_existente.get_estado_display()}).",
                )
                return redirect("home")

        # ── 4. Crear reserva en estado 'pendiente_pago' si no existe ────────
        if not reserva:
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
        try:
            # Construimos la URL base absoluta sin el querystring y lo concatenamos manualmente
            # para evitar que build_absolute_uri URL-codifique las llaves {} que necesita Stripe.
            base_url = request.build_absolute_uri(reverse("booking_success"))
            success_url = f"{base_url}?reserva_id={reserva.pk}&session_id={{CHECKOUT_SESSION_ID}}"
            
            cancel_url = request.build_absolute_uri(reverse("home") + "?reserva_cancelada=1")

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
                success_url=success_url,
                cancel_url=cancel_url,
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


class ReservaSuccessView(LoginRequiredMixin, View):
    """
    Vista de retorno tras un pago exitoso en Stripe.

    Stripe redirige aquí con ?reserva_id=X&session_id=cs_test_...
    Verificamos directamente con la API de Stripe que el pago está 'paid'
    y confirmamos la reserva en base de datos.

    Esto hace el flujo funcional en desarrollo local sin necesidad de webhook.
    En producción, el webhook también confirma (doble seguridad).
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        reserva_id = request.GET.get("reserva_id")
        session_id = request.GET.get("session_id")

        if not reserva_id or not session_id:
            messages.warning(request, "Parámetros de pago incompletos.")
            return redirect("home")

        try:
            reserva = Reserva.objects.get(pk=reserva_id, usuario=request.user)
        except Reserva.DoesNotExist:
            messages.error(request, "Reserva no encontrada.")
            return redirect("home")

        # Ya confirmada (p.ej. llegó el webhook antes que esta vista)
        if reserva.estado == "confirmada":
            messages.success(request, f"¡Tu reserva para «{reserva.clase.title}» ya está confirmada!")
            return redirect(reverse("home") + "?reserva_ok=1")

        # Verificar con Stripe que el pago está realmente completado
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                reserva.estado = "confirmada"
                reserva.save(update_fields=["estado"])
                messages.success(
                    request,
                    f"¡Reserva confirmada! «{reserva.clase.title}» está en tu lista de clases.",
                )
                return redirect(reverse("home") + "?reserva_ok=1")
            else:
                messages.warning(
                    request,
                    "El pago aún no está procesado. Espera unos segundos y recarga.",
                )
                return redirect("home")
        except Exception as e:
            messages.error(request, f"Error al verificar el pago: {e}")
            return redirect("home")
