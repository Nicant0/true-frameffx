from django.views.generic import TemplateView
from django.shortcuts import redirect


class LandingView(TemplateView):
    """
    Página de bienvenida pública (Landing Page).
    Accesible para invitados y usuarios autenticados.
    Si el usuario ya tiene sesión iniciada, se redirige al panel principal.
    """
    template_name = "portfolio/landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("products:showProducts")
        return super().dispatch(request, *args, **kwargs)

from django.db.models import Sum
from django.utils import timezone
from users.mixins import StaffRequiredMixin
from users.models import Usuario
from products.models import Pedido
from bookings.models import Reserva

class AdminDashboardView(StaffRequiredMixin, TemplateView):
    """
    Panel de control exclusivo para administradores (Staff).
    Proporciona métricas en tiempo real.
    """
    template_name = "portfolio/dashboard_admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Métricas de Usuarios
        context["total_usuarios"] = Usuario.objects.count()
        context["usuarios_activos"] = Usuario.objects.filter(is_active=True).count()
        
        # Métricas de Ventas
        ingresos_pedidos = Pedido.objects.filter(estado="completado").aggregate(total_sum=Sum("total"))["total_sum"] or 0
        ingresos_reservas = Reserva.objects.filter(estado="confirmada").aggregate(total_sum=Sum("clase__price"))["total_sum"] or 0
        
        context["total_ingresos"] = ingresos_pedidos + ingresos_reservas
        context["ultimos_pedidos"] = Pedido.objects.all().select_related("usuario").order_by("-fecha_creacion")[:5]
        
        # Métricas de Reservas
        now = timezone.now()
        context["reservas_pendientes"] = Reserva.objects.filter(
            estado__in=["pendiente", "pendiente_pago"]
        ).count()
        context["proximas_clases"] = Reserva.objects.filter(
            clase__start_at__gte=now,
            estado__in=["pendiente", "pendiente_pago", "confirmada"],
        ).select_related("clase", "usuario").order_by("clase__start_at")[:5]
        
        return context
