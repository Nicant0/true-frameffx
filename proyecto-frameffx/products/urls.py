from django.urls import path
from .views import showProducts
from .checkout_views import CreateCheckoutSessionView, StripeWebhookView, DownloadProductView

app_name = 'products'

urlpatterns = [
    path('', showProducts.as_view(), name='showProducts'),
    path('checkout/<int:pk>/', CreateCheckoutSessionView.as_view(), name='checkout_session'),
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('download/<int:pk>/', DownloadProductView.as_view(), name='download_product'),
]
