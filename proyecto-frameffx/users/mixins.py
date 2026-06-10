from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden


class StaffRequiredMixin(LoginRequiredMixin):
    """
    Solo usuarios staff pueden acceder.
    Redirige al login si no está autenticado, devuelve 403 si no es staff.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            return HttpResponseForbidden("No tienes permisos")
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class SetPasswordMixin:
    """
    Se encarga de gestionar la contraseña en formularios Create/Update.
    """
    password_field = "password"

    def form_valid(self, form):
        usuario = form.save(commit=False)

        password = self.request.POST.get(self.password_field)
        if password:
            usuario.set_password(password)

        usuario.save()
        return super().form_valid(form)
