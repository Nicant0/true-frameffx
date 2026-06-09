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
        queryset = Producto.objects.filter(publicado=True)
        
        orden = self.request.GET.get("orden", "recientes")
        dir = self.request.GET.get("dir", "desc")
        
        ordenes_permitidos = {
            "titulo": "titulo",
            "precio": "precio",
            "recientes": "fecha_creacion",
        }
        
        campo_orden = ordenes_permitidos.get(orden, "fecha_creacion")
        if dir == "desc":
            campo_orden = "-" + campo_orden

        return queryset.order_by(campo_orden)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orden"] = self.request.GET.get("orden", "recientes")
        context["dir"] = self.request.GET.get("dir", "desc")
        return context


# ── CRUD Admin ────────────────────────────────────────────────────────────────

class ProductoListAdminView(StaffRequiredMixin, ListView):
    """Listado de todos los productos para el administrador."""
    model = Producto
    template_name = 'products/producto_list.html'
    context_object_name = 'productos'

    def get_queryset(self):
        queryset = Producto.objects.all()
        
        sort = self.request.GET.get("sort", "fecha_creacion")
        dir = self.request.GET.get("dir", "desc")
        
        sort_permitidos = ["id", "titulo", "precio", "publicado", "fecha_creacion"]
        if sort not in sort_permitidos:
            sort = "fecha_creacion"
            
        campo_orden = sort
        if dir == "desc":
            campo_orden = "-" + sort
            
        return queryset.order_by(campo_orden)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sort"] = self.request.GET.get("sort", "fecha_creacion")
        context["dir"] = self.request.GET.get("dir", "desc")
        return context


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
