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

from .forms import RegistroForm
from .models import Usuario
from .mixins import StaffRequiredMixin, SetPasswordMixin


# ── Registro público ──────────────────────────────────────────────────────────

class SignupView(TemplateView):
    """
    Controlador (Vista) para el registro público de nuevos usuarios.

    He creado esta vista basándome en TemplateView en lugar de FormView o CreateView 
    para poder controlar manualmente en el método `post` el inicio de sesión 
    automático tras un registro exitoso, mejorando así la experiencia de usuario.
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
        # Proceso manualmente los datos enviados en el formulario de registro
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()                      # Guardo el usuario (contraseña encriptada)
            login(request, user,                    # Fuerzo el inicio de sesión automático
                  backend="django.contrib.auth.backends.ModelBackend")
            return redirect("home")
        # Si hay errores, devuelvo la plantilla con los errores para que el usuario corrija
        return render(request, self.template_name, {"form": form})


class UsuariosListView(StaffRequiredMixin, ListView):
    """Vista que he creado exclusiva para que el Staff (Admin) liste los usuarios."""
    model = Usuario
    template_name = "users/usuarios_list.html"
    context_object_name = "usuarios"

class UsuariosCreateView(StaffRequiredMixin, SetPasswordMixin, CreateView):
    """Vista exclusiva para que el Staff cree manualmente un usuario desde el panel."""
    model = Usuario
    fields = ["username", "email", "activo"]
    template_name = "users/usuarios_form.html"
    success_url = reverse_lazy("usuarios_list")

class UsuariosUpdateView(StaffRequiredMixin, SetPasswordMixin, UpdateView):
    """Permite al Staff actualizar los datos (incluyendo contraseñas mediante el mixin) de un usuario."""
    model = Usuario
    fields = ["username", "email", "activo"]
    template_name = "users/usuarios_form.html"
    success_url = reverse_lazy("usuarios_list")

class UsuariosDeleteView(StaffRequiredMixin, DeleteView):
    """Vista exclusiva de Staff para eliminar (baja lógica o física) a un usuario."""
    model = Usuario
    template_name = "users/usuarios_confirm_delete.html"
    success_url = reverse_lazy("usuarios_list")

class HomeView(TemplateView):
    template_name = "portfolio/home.html"
    login_url = '/'

class LoginView(TemplateView):
    template_name = "portfolio/login.html"
