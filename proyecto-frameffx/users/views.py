from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    CreateView,
    UpdateView,
    DeleteView,
    ListView
)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .forms import RegistroForm, UserProfileForm
from .models import Usuario
from .mixins import StaffRequiredMixin, SetPasswordMixin
from common.utils import get_pedidos_completados_para_usuario


# Vistas de gestión de usuarios

class SignupView(TemplateView):
    """
    Vista para el registro público de nuevos usuarios.

    Extiende TemplateView en lugar de FormView o CreateView para controlar
    manualmente en el método post el inicio de sesión automático tras un
    registro exitoso, mejorando la experiencia de usuario.
    """
    template_name = "portfolio/signup.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = RegistroForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()                      # Guarda el usuario con la contraseña encriptada
            login(request, user,                    # Inicia la sesión automáticamente tras el registro
                  backend="django.contrib.auth.backends.ModelBackend")
            return redirect("home")
        # Si el formulario tiene errores, lo devuelve con los mensajes de validación
        return render(request, self.template_name, {"form": form})


class UsuariosListView(StaffRequiredMixin, ListView):
    """Listado de todos los usuarios del sistema, accesible solo para el staff."""
    model = Usuario
    template_name = "users/usuarios_list.html"
    context_object_name = "usuarios"

    def get_queryset(self):
        queryset = Usuario.objects.all()
        
        sort = self.request.GET.get("sort", "id")
        dir = self.request.GET.get("dir", "asc")
        
        sort_permitidos = ["id", "email", "is_active", "create_date"]
        if sort not in sort_permitidos:
            sort = "id"
            
        campo_orden = sort
        if sort == "create_date":
            campo_orden = "create_date"
            
        if dir == "desc":
            campo_orden = "-" + campo_orden
            
        return queryset.order_by(campo_orden)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sort"] = self.request.GET.get("sort", "id")
        context["dir"] = self.request.GET.get("dir", "asc")
        return context

class UsuariosCreateView(StaffRequiredMixin, SetPasswordMixin, CreateView):
    """Vista exclusiva para el staff para crear manualmente un nuevo usuario desde el panel."""
    model = Usuario
    fields = ["username", "email", "is_active"]
    template_name = "users/usuarios_form.html"
    success_url = reverse_lazy("usuarios_list")

class UsuariosUpdateView(StaffRequiredMixin, SetPasswordMixin, UpdateView):
    """Permite al staff actualizar los datos de un usuario, incluyendo su contraseña mediante el mixin."""
    model = Usuario
    fields = ["username", "email", "is_active"]
    template_name = "users/usuarios_form.html"
    success_url = reverse_lazy("usuarios_list")

from django.db.models import ProtectedError

class UsuariosDeleteView(StaffRequiredMixin, DeleteView):
    """Vista exclusiva del staff para eliminar un usuario del sistema."""
    model = Usuario
    template_name = "users/usuarios_confirm_delete.html"
    success_url = reverse_lazy("usuarios_list")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Usuario eliminado correctamente.")
            return response
        except ProtectedError:
            messages.error(
                self.request,
                "No se puede eliminar este usuario porque tiene pedidos o reservas asociados en el sistema. "
                "Para preservar la integridad contable, por favor, desactívalo desmarcando la opción "
                "'Activo' en lugar de eliminarlo."
            )
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(self.get_success_url())


class UserProfileView(LoginRequiredMixin, UpdateView):
    """
    Permite al usuario autenticado editar los datos de su perfil.
    """
    model = Usuario
    form_class = UserProfileForm
    template_name = "users/profile.html"
    success_url = reverse_lazy("user_profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Tu perfil ha sido actualizado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pedidos_completados"] = get_pedidos_completados_para_usuario(self.request.user)
        return context
