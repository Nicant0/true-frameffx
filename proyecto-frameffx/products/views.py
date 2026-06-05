# Inter_7.a – Vistas de Marketplace (pública) y gestión admin (CRUD)
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Producto
from .forms import ProductoForm
from users.mixins import StaffRequiredMixin


# ── Vista pública ─────────────────────────────────────────────────────────────

class showProducts(ListView):
    model = Producto
    template_name = 'portfolio/products.html'
    context_object_name = 'productos'

    def get_queryset(self):
        return Producto.objects.filter(publicado=True)


# ── CRUD Admin ────────────────────────────────────────────────────────────────

class ProductoListAdminView(StaffRequiredMixin, ListView):
    """Listado de todos los productos para el administrador."""
    model = Producto
    template_name = 'products/producto_list.html'
    context_object_name = 'productos'
    queryset = Producto.objects.all().order_by('-fecha_creacion')


class ProductoCreateView(StaffRequiredMixin, CreateView):
    """Crear un nuevo producto en el marketplace."""
    model = Producto
    form_class = ProductoForm
    template_name = 'products/producto_form.html'
    success_url = reverse_lazy('products:product_list_admin')

    def form_valid(self, form):
        messages.success(self.request, "Producto creado correctamente.")
        return super().form_valid(form)


class ProductoUpdateView(StaffRequiredMixin, UpdateView):
    """Editar un producto existente."""
    model = Producto
    form_class = ProductoForm
    template_name = 'products/producto_form.html'
    success_url = reverse_lazy('products:product_list_admin')

    def form_valid(self, form):
        messages.success(self.request, "Producto actualizado correctamente.")
        return super().form_valid(form)


class ProductoDeleteView(StaffRequiredMixin, DeleteView):
    """Confirmar y eliminar un producto."""
    model = Producto
    template_name = 'products/producto_confirm_delete.html'
    success_url = reverse_lazy('products:product_list_admin')

    def form_valid(self, form):
        messages.success(self.request, "Producto eliminado correctamente.")
        return super().form_valid(form)
