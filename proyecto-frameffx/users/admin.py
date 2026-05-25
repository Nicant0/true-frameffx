from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import Usuario

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ('email', 'username', 'activo')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = ('email', 'username', 'activo')

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    model = Usuario
    
    list_display = ('email', 'username', 'is_active', 'is_staff', 'activo', 'create_date')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'activo')
    search_fields = ('email', 'username')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'activo', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password', 'is_staff', 'is_active', 'activo'),
        }),
    )

admin.site.register(Usuario, CustomUserAdmin)
