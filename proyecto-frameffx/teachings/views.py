from django.contrib import messages
from django.db import DatabaseError, IntegrityError
from django.db.models import Q, ProtectedError
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from bookings.models import Reserva
from users.mixins import StaffRequiredMixin
from common.utils import get_pedidos_completados_para_usuario
from products.models import Pedido

from .form import TeachingForm
from .models import Teaching


class showTeachings(ListView):
    """
    Vista principal del catálogo de clases virtuales.
    
    Unifica la lógica de visualización para tres tipos de perfil:
    - Staff y administradores: ven todo el catálogo histórico con filtros avanzados.
    - Usuarios autenticados: ven solo clases activas cruzadas con su historial de reservas.
    - Invitados anónimos: ven el catálogo público sin datos personales.
    """

    model = Teaching
    template_name = "portfolio/home.html"
    context_object_name = "teachings"
    paginate_by = 9

    def get_template_names(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return ["portfolio/home.html"]
        return ["portfolio/home_user.html"]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            queryset = Teaching.objects.all()
        else:
            queryset = Teaching.objects.filter(estado="activa", start_at__gt=timezone.now())

        titulo = self.request.GET.get("titulo")
        if titulo:
            queryset = queryset.filter(title__icontains=titulo)

        estado = self.request.GET.get("estado")
        if estado and user.is_authenticated and user.is_staff:
            queryset = queryset.filter(estado=estado)

        orden = self.request.GET.get("orden", "recientes")
        dir = self.request.GET.get("dir", "desc")
        
        ordenes_permitidos = {
            "titulo": "title",
            "precio": "price",
            "fecha": "start_at",
            "recientes": "fecha_creacion",
        }
        
        campo_orden = ordenes_permitidos.get(orden, "fecha_creacion")
        if dir == "desc":
            campo_orden = "-" + campo_orden

        return queryset.order_by(campo_orden)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = self.request.GET.get("titulo", "")
        context["estado"] = self.request.GET.get("estado", "")
        context["orden"] = self.request.GET.get("orden", "recientes")
        context["dir"] = self.request.GET.get("dir", "desc")

        # Inyecta el historial de reservas solo para usuarios autenticados que no sean staff
        user = self.request.user
        if user.is_authenticated and not user.is_staff:
            reservas_usuario = (
                Reserva.objects.select_related("clase")
                .filter(usuario=user)
                .exclude(estado__in=["cancelada", "caducada"])
            )
            reservas_ids = reservas_usuario.values_list("clase_id", flat=True)

            context["reservas_ids"] = set(reservas_ids)
            context["reservas_activas"] = reservas_usuario.filter(
                ~Q(clase__estado="finalizada"),
                clase__end_at__gte=timezone.now()
            ).order_by("clase__start_at")
            context["reservas_finalizadas"] = reservas_usuario.filter(
                Q(clase__estado="finalizada") | Q(clase__end_at__lt=timezone.now())
            ).order_by("-clase__end_at")

            # Incluye los pedidos con sus líneas de detalle
            context["pedidos_completados"] = get_pedidos_completados_para_usuario(user)
        else:
            # Inyecta variables seguras cuando el usuario no está autenticado o es staff
            context["reservas_ids"] = set()
            context["reservas_activas"] = Reserva.objects.none()
            context["reservas_finalizadas"] = Reserva.objects.none()
            context["pedidos_completados"] = Pedido.objects.none()

        return context


class TeachingCreateView(StaffRequiredMixin, CreateView):
    """
    Vista exclusiva para staff encargada de la creación de nuevas clases en el catálogo.
    Captura excepciones de integridad para gestionar clases duplicadas en el mismo horario.
    """
    model = Teaching
    form_class = TeachingForm
    template_name = "portfolio/teaching_form.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f"La clase «{self.object.title}» ha sido creada con éxito.")
            return response
        except IntegrityError:
            messages.error(self.request, "Error: Ya existe una clase con este título en la misma fecha y hora.")
            return self.form_invalid(form)
        except DatabaseError:
            messages.error(self.request, "Ocurrió un error en la base de datos al crear la clase.")
            return self.form_invalid(form)


class TeachingDetailView(StaffRequiredMixin, DetailView):
    """
    Detalle completo de la clase, reservado solo para uso administrativo.
    """
    model = Teaching
    template_name = "portfolio/teaching_detail.html"
    context_object_name = "teaching"


class TeachingUpdateView(StaffRequiredMixin, UpdateView):
    """
    Permite al staff actualizar los datos de una clase.
    Captura excepciones para evitar errores si los datos introducidos incumplen reglas de base de datos.
    """
    model = Teaching
    form_class = TeachingForm
    template_name = "portfolio/teaching_form.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f"La clase «{self.object.title}» ha sido actualizada.")
            return response
        except IntegrityError:
            messages.error(self.request, "Error de integridad: Ya existe otra clase idéntica en este horario.")
            return self.form_invalid(form)
        except DatabaseError:
            messages.error(self.request, "Ocurrió un error de base de datos al intentar actualizar la clase.")
            return self.form_invalid(form)


class TeachingDeleteView(StaffRequiredMixin, DeleteView):
    """
    Elimina permanentemente una clase del sistema.
    Sobreescribe form_valid para mostrar un mensaje con el título de la clase eliminada.
    """
    model = Teaching
    template_name = "portfolio/teaching_confirm_delete.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        # DeleteView usa form_valid para manejar el borrado en las versiones recientes de Django
        try:
            # Recupera el objeto antes de borrarlo para usarlo en el mensaje de confirmación
            self.object = self.get_object()
            titulo = self.object.title
            response = super().form_valid(form)
            messages.success(self.request, f"La clase «{titulo}» ha sido eliminada permanentemente.")
            return response
        except ProtectedError:
            messages.error(
                self.request,
                "No se puede eliminar esta clase porque tiene reservas asociadas. "
                "Para mantener la integridad contable de los pagos, cambia su estado "
                "a 'Cancelada' o 'Finalizada' en lugar de eliminarla."
            )
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(self.get_success_url())
        except DatabaseError:
            messages.error(self.request, "No se pudo eliminar la clase por un error interno de base de datos.")
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(self.get_success_url())

