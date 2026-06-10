from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from login.views import LoginFormView, Logout
from common.views import LandingView, AdminDashboardView
from django.conf import settings
from django.conf.urls.static import static

from users import views
from bookings.views import ReservaCreateView, ReservaCancelView
from bookings.checkout_views import ReservaCheckoutView, ReservaSuccessView
from teachings.api.views import (
    TeachingViewSet,
    TeachingAuthenticatedListViewSet,
    TeachingCRUDView,
)
from teachings.views import (
    showTeachings,
    TeachingCreateView,
    TeachingDetailView,
    TeachingUpdateView,
    TeachingDeleteView
)

# Router de la API para exponer los endpoints de clases (Teachings) automáticamente
router = routers.DefaultRouter()
router.register('teachings', TeachingViewSet, basename='teachings')
router.register('teachings-auth', TeachingAuthenticatedListViewSet, basename='teachings-auth')
router.register('teachings-crud', TeachingCRUDView, basename='teachings-crud')

urlpatterns = [
    # Panel de administración por defecto de Django
    path('admin/', admin.site.urls),
    
    # Panel de control analítico para administradores
    path('dashboard-admin/', AdminDashboardView.as_view(), name='admin_dashboard'),

    # Landing page
    path('', LandingView.as_view(), name='landing'),

    # Autenticación
    path('login/', LoginFormView.as_view(), name='site_login'),
    path('accounts/login/', LoginFormView.as_view(), name='accounts_login'),
    path('logout/', Logout.as_view(), name="site_logout"),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('accounts/signup/', views.SignupView.as_view(), name='account_signup'),

    # Vistas principales
    # Home: catálogo principal de clases
    path('home/', showTeachings.as_view(), name='home'),
    
    # URLs de la app de productos digitales
    path('products/', include('products.urls')),

    # CRUD Teaching
    path('teachings/create/', TeachingCreateView.as_view(), name='teaching_create'),
    path('teachings/<int:pk>/', TeachingDetailView.as_view(), name='teaching_detail'),
    path('teachings/<int:pk>/update/', TeachingUpdateView.as_view(), name='teaching_update'),
    path('teachings/<int:pk>/delete/', TeachingDeleteView.as_view(), name='teaching_delete'),

    # CRUD Usuarios
    path('perfil/', views.UserProfileView.as_view(), name='user_profile'),
    path('usuarios/create/', views.UsuariosCreateView.as_view(), name='usuarios_create'),
    path('usuarios/update/<int:pk>/', views.UsuariosUpdateView.as_view(), name='usuarios_update'),
    path('usuarios/delete/<int:pk>/', views.UsuariosDeleteView.as_view(), name='usuarios_delete'),
    path('usuarios/', views.UsuariosListView.as_view(), name='usuarios_list'),

    # Bookings
    path('bookings/create/', ReservaCreateView.as_view(), name='booking_create'),
    path('bookings/<int:pk>/cancel/', ReservaCancelView.as_view(), name='booking_cancel'),
    path('bookings/<int:pk>/checkout/', ReservaCheckoutView.as_view(), name='booking_checkout'),
    path('bookings/success/', ReservaSuccessView.as_view(), name='booking_success'),

    # Autenticación con terceros (Google OAuth via allauth)
    path('accounts/', include('allauth.urls')),

    # Endpoints de la API REST
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/', include('djoser.urls.authtoken')),
]

# Configuración para servir archivos estáticos en entorno local (DEBUG=True)
if settings.DEBUG:
    _static_dirs = getattr(settings, 'STATICFILES_DIRS', None)
    if _static_dirs and isinstance(_static_dirs, list):
        urlpatterns += static(settings.STATIC_URL, document_root=_static_dirs[0])
    elif getattr(settings, 'STATIC_ROOT', None):
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
