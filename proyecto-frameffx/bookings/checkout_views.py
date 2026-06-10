"""
bookings/checkout_views.py
Gestiona el flujo de pago Stripe para la reserva de clases virtuales.

Flujo de vida de la reserva:
  1. El usuario hace POST a ReservaCheckoutView.
  2. Se verifica que la clase esté activa y que el usuario no tenga ya una reserva.
  3. Se crea un registro en la BD con estado='pendiente_pago'.
  4. Se inicia una sesión de Stripe Checkout y se redirige al usuario.
  5a. (Producción) El webhook asíncrono actualiza la Reserva a 'confirmada'.
  5b. (Desarrollo/Demo) ReservaSuccessView verifica la sesión directamente con la API
      de Stripe y confirma la reserva sin necesidad de webhook local.
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

    Aplica tres validaciones previas para proteger la integridad de los datos:
      1. Los administradores no pueden reservar clases.
      2. La clase debe seguir en estado 'activa'.
      3. Se comprueba que el usuario no tenga ya una reserva activa para esa clase.

    Si las validaciones son correctas, crea la Reserva en estado 'pendiente_pago'
    y redirige a Stripe.
    """

    http_method_names = ["post"]

    def post(self, request, pk, *args, **kwargs):
        # 1. Admins no reservan
        if request.user.is_staff:
            messages.error(request, "Los administradores no pueden realizar reservas.")
            return redirect("home")

        # 2. La clase existe y está activa
        clase = get_object_or_404(Teaching, pk=pk)
        if not clase.is_active_now:
            messages.warning(
                request,
                f"La clase «{clase.title}» ya no está disponible para reservar "
                f"(estado o fecha finalizados).",
            )
            return redirect("home")

        # 3. No duplicar reserva activa y reciclar canceladas
        reserva_existente = Reserva.objects.filter(
            clase=clase,
            usuario=request.user,
        ).first()

        reserva = None

        if reserva_existente:
            if reserva_existente.estado == "confirmada":
                messages.info(
                    request,
                    f"Ya tienes una reserva confirmada para «{clase.title}».",
                )
                return redirect("home")
            elif reserva_existente.estado in ["pendiente_pago", "pendiente"]:
                # Se reutiliza la reserva pendiente en lugar de bloquear al usuario
                reserva = reserva_existente
            elif reserva_existente.estado in ["cancelada", "caducada"]:
                # RECICLAJE: La base de datos tiene unique_together(clase, usuario)
                # No podemos crear una nueva, así que reactivamos la antigua
                reserva = reserva_existente
                reserva.estado = "pendiente_pago"
                reserva.save(update_fields=["estado"])
                
        # 4. Crear reserva en estado 'pendiente_pago' si no existe
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

        # 4.5. Si la clase es gratis, confirmar directamente sin pasar por Stripe
        if clase.price <= 0:
            reserva.estado = "confirmada"
            reserva.save(update_fields=["estado"])
            messages.success(request, f"¡Reserva confirmada! Tu plaza para «{clase.title}» es gratuita.")
            return redirect(reverse("home") + "?reserva_ok=1")

        # 5. Crear sesión de Stripe
        try:
            # La URL base se construye sin querystring y se concatena manualmente
            # para evitar que build_absolute_uri codifique las llaves {} que necesita Stripe
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
            # Si Stripe falla, se elimina la reserva para evitar registros huérfanos
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
    Verifica directamente con la API de Stripe que el pago esté en estado 'paid'
    y confirma la reserva en base de datos.

    Esto hace el flujo funcional en desarrollo local sin necesidad de webhook.
    En producción, el webhook también confirma la reserva para mayor seguridad.
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

        if reserva.estado == "confirmada":
            messages.success(request, f"¡Tu reserva para «{reserva.clase.title}» ya está confirmada!")
            return redirect(reverse("home") + "?reserva_ok=1")

        # Verifica con Stripe que el pago está realmente completado
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid" and session.get('client_reference_id') == f"reserva:{reserva.pk}":
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
