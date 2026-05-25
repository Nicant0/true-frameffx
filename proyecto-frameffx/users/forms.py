from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Usuario


class RegistroForm(forms.Form):
    """
    Formulario de registro público para nuevos usuarios (Signup).

    Este formulario valida que el correo electrónico no esté duplicado,
    aplica las validaciones de seguridad de contraseña definidas en Django,
    y verifica que ambas contraseñas coincidan. Utiliza el modelo Usuario
    personalizado (email como USERNAME_FIELD).
    """

    nombre = forms.CharField(
        label="Nombre o apodo",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            "id": "id_nombre",
            "placeholder": "Tu nombre o apodo (opcional)",
            "autocomplete": "name",
        }),
    )

    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "id": "id_email",
            "placeholder": "correo@ejemplo.com",
            "autocomplete": "email",
        }),
    )

    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "id": "id_password1",
            "placeholder": "Mínimo 8 caracteres",
            "autocomplete": "new-password",
        }),
    )

    password2 = forms.CharField(
        label="Confirmar contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "id": "id_password2",
            "placeholder": "Repite la contraseña",
            "autocomplete": "new-password",
        }),
    )

    # ── Validaciones ─────────────────────────────────────────────

    def clean_email(self):
        """Verifica que el email no esté ya registrado."""
        email = self.cleaned_data["email"].lower()
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError(
                "Ya existe una cuenta con este correo electrónico."
            )
        return email

    def clean_password1(self):
        """Aplica los validadores de contraseña de Django (settings.AUTH_PASSWORD_VALIDATORS)."""
        password = self.cleaned_data.get("password1")
        if password:
            validate_password(password)
        return password

    def clean(self):
        """Comprueba que ambas contraseñas coincidan."""
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned

    # ── Creación del usuario ──────────────────────────────────────

    def save(self):
        """
        Crea y devuelve el nuevo usuario con:
          - is_active = True  → puede iniciar sesión de inmediato.
          - is_staff  = False → rol de usuario estándar (no admin).
          - contraseña encriptada vía set_password().
        """
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
        nombre = self.cleaned_data.get("nombre", "")

        user = Usuario(
            email=email,
            username=nombre or None,
            is_active=True,   # rol usuario estándar: puede acceder a vistas protegidas
            is_staff=False,   # no tiene acceso al panel de administración
        )
        user.set_password(password)   # encripta la contraseña con PBKDF2
        user.save()
        return user
