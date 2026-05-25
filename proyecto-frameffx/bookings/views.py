from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError, IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from teachings.models import Teaching

from .models import Reserva


class ReservaCreateView(LoginRequiredMixin, View):
    """
    Vista para crear una nueva reserva de una clase virtual.

    Valida que el usuario sea elegible y que la clase esté disponible
    antes de crear el registro en la base de datos. Está protegida contra
    errores de integridad o caídas de base de datos.

    Reglas de validación:
    1. El usuario debe estar autenticado (LoginRequiredMixin redirige al login).
    2. Los administradores (is_staff) no pueden reservar sus propias clases.
    3. La clase debe existir y tener estado 'activa'.
    4. El usuario no puede tener ya una reserva activa para esa misma clase
       (se considera activa si no está en 'cancelada' ni 'caducada').
    """

    http_method_names = ["post"]  # Solo acepta POST; GET devuelve 405

    def post(self, request, *args, **kwargs):
        # ── Validación 1: admins no reservan ──────────────────────────────────
        if request.user.is_staff:
            messages.error(request, "Los administradores no pueden realizar reservas.")
            return redirect("home")

        # ── Validación 2: la clase existe y está activa ───────────────────────
        clase = get_object_or_404(Teaching, pk=request.POST.get("clase_id"))
        if clase.estado != "activa":
            messages.warning(
                request,
                f"La clase «{clase.title}» ya no está disponible para reservar "
                f"(estado: {clase.get_estado_display()}).",
            )
            return redirect("home")

        # ── Validación 3: no duplicar reserva activa ──────────────────────────
        reserva_existente = Reserva.objects.filter(
            clase=clase,
            usuario=request.user,
        ).exclude(estado__in=["cancelada", "caducada"]).first()

        if reserva_existente:
            messages.info(
                request,
                f"Ya tienes una reserva activa para «{clase.title}» "
                f"(estado: {reserva_existente.get_estado_display()}).",
            )
            return redirect("home")

        # ── Crear la reserva ──────────────────────────────────────────────────
        try:
            Reserva.objects.create(
                clase=clase,
                usuario=request.user,
                estado="pendiente",
            )
            messages.success(
                request,
                f"¡Reserva para «{clase.title}» realizada con éxito! "
                "Recibirás la confirmación por correo electrónico.",
            )
        except IntegrityError:
            messages.error(
                request, 
                "Hubo un conflicto de datos y no se pudo completar la reserva. "
                "Es posible que esta reserva ya exista."
            )
        except DatabaseError:
            messages.error(
                request,
                "Ocurrió un error en el servidor al intentar crear la reserva. "
                "Por favor, inténtalo de nuevo más tarde."
            )

        return redirect("home")


class ReservaCancelView(LoginRequiredMixin, View):
    """
    Vista para cancelar una reserva existente del usuario autenticado.

    Solo permite la cancelación si la reserva está en estado 'pendiente'
    o 'confirmada'. Implementa manejo de excepciones de base de datos.
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        reserva = get_object_or_404(
            Reserva,
            pk=kwargs.get("pk"),
            usuario=request.user,  # Garantiza que solo cancela SUS reservas
        )

        if reserva.estado not in ["pendiente", "confirmada"]:
            messages.warning(
                request,
                "Esta reserva no puede cancelarse porque ya está "
                f"en estado «{reserva.get_estado_display()}».",
            )
            return redirect("home")

        reserva.estado = "cancelada"
        
        try:
            reserva.save(update_fields=["estado"])
            messages.success(request, f"Reserva para «{reserva.clase.title}» cancelada correctamente.")
        except DatabaseError:
            messages.error(
                request,
                "Error interno de base de datos al intentar cancelar la reserva. "
                "Por favor, contacta con soporte o intenta de nuevo."
            )

        return redirect("home")
