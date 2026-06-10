from django.urls import path
from .views import (
    showProducts,
    ProductoListAdminView,
    ProductoCreateView,
    ProductoUpdateView,
    ProductoDeleteView,
)
from .checkout_views import CreateCheckoutSessionView, StripeWebhookView, DownloadProductView, ProductSuccessView

app_name = 'products'

urlpatterns = [
    # ── Marketplace público ──
    path('', showProducts.as_view(), name='showProducts'),
    path('checkout/<int:pk>/', CreateCheckoutSessionView.as_view(), name='checkout_session'),
    path('checkout/success/', ProductSuccessView.as_view(), name='product_success'),
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('download/<int:pk>/', DownloadProductView.as_view(), name='download_product'),

    # ── CRUD Admin ──
    path('admin/', ProductoListAdminView.as_view(), name='product_list_admin'),
    path('admin/crear/', ProductoCreateView.as_view(), name='product_create'),
    path('admin/<int:pk>/editar/', ProductoUpdateView.as_view(), name='product_update'),
    path('admin/<int:pk>/eliminar/', ProductoDeleteView.as_view(), name='product_delete'),
]
