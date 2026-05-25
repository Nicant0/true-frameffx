from django.test import TestCase
from django.urls import reverse
from users.models import Usuario
from users.forms import RegistroForm

class RegistroFormTests(TestCase):
    """
    Pruebas unitarias para el formulario de registro y creación de usuarios.
    Verifica que la lógica de negocio (validaciones y cifrado) funciona
    correctamente, asegurando la robustez de la aplicación.
    """

    def setUp(self):
        """
        Configuración inicial antes de cada prueba.
        Creamos un usuario base para probar duplicados.
        """
        self.usuario_existente = Usuario.objects.create_user(
            email="test@frameffx.com",
            password="testpassword123",
            username="TestUser"
        )
        self.form_data = {
            "nombre": "NuevoUsuario",
            "email": "nuevo@frameffx.com",
            "password1": "SecurePass2026!",
            "password2": "SecurePass2026!"
        }

    def test_registro_exitoso(self):
        """
        Prueba que un formulario válido crea un usuario correctamente,
        y que is_active y is_staff se configuran como se espera.
        """
        form = RegistroForm(data=self.form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, "nuevo@frameffx.com")
        self.assertEqual(user.username, "NuevoUsuario")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_encriptacion_contraseña(self):
        """
        Prueba que la contraseña del nuevo usuario se encripta
        y no se guarda en texto plano en la base de datos.
        """
        form = RegistroForm(data=self.form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        # Verificar que la contraseña encriptada no sea igual al texto plano
        self.assertNotEqual(user.password, "SecurePass2026!")
        # Verificar que Django puede validar la contraseña correctamente
        self.assertTrue(user.check_password("SecurePass2026!"))

    def test_rechazo_email_duplicado(self):
        """
        Prueba que el formulario rechaza el registro si se usa
        un correo electrónico que ya existe en la base de datos.
        """
        data = self.form_data.copy()
        data["email"] = "test@frameffx.com"  # Email del setUp
        
        form = RegistroForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(
            form.errors["email"][0],
            "Ya existe una cuenta con este correo electrónico."
        )

    def test_contraseñas_no_coinciden(self):
        """
        Prueba que el formulario falla si password1 y password2 son diferentes.
        """
        data = self.form_data.copy()
        data["password2"] = "DiferentePass!"
        
        form = RegistroForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        self.assertEqual(
            form.errors["password2"][0],
            "Las contraseñas no coinciden."
        )
