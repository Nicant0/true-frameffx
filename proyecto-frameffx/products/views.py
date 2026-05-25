# Inter_7.a – Vista para mostrar productos
from django.views.generic import ListView
from .models import Producto


class showProducts(ListView):
    model = Producto
    template_name = 'portfolio/products.html'
    context_object_name = 'productos'
    
    def get_queryset(self):
        return Producto.objects.filter(publicado=True)
