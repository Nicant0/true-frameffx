from products.models import Pedido

def get_pedidos_completados_para_usuario(user):
    """
    Devuelve el queryset de pedidos completados para un usuario,
    con los prefetch necesarios para optimizar las consultas.
    """
    return (
        Pedido.objects
        .filter(usuario=user, estado="completado")
        .prefetch_related("detalles__producto", "detalles__descargas")
        .order_by("-fecha_creacion")
    )
