from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden


class StaffRequiredMixin(LoginRequiredMixin):
    """
    Solo usuarios staff pueden acceder.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("No tienes permisos")
        return super().dispatch(request, *args, **kwargs)


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
