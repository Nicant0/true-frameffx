from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import redirect


class LoginFormView(LoginView):
    """
    Controlador para el inicio de sesión.
    Heredo de la vista genérica LoginView de Django, y configuro `redirect_authenticated_user`
    para que si un usuario ya logeado intenta entrar aquí, sea redirigido al Home automáticamente.
    """
    template_name = "portfolio/login.html"
    redirect_authenticated_user = True
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Iniciar sesion"
        return context

    def get_success_url(self):
        return str(self.success_url)


class Logout(LogoutView):
    """
    Controlador para cerrar sesión.
    Me aseguro de que el usuario vuelva a la pantalla de login una vez cierra sesión.
    """
    next_page = reverse_lazy("site_login")

    def get_success_url(self):
        return str(self.next_page)
