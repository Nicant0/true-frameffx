import os
import stripe
import stripe.error
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse, HttpResponse, FileResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import Producto, Pedido, DetallePedido, Descarga
from bookings.models import Reserva

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(LoginRequiredMixin, View):
    """
    Inicializa la sesión de pago con Stripe para un producto digital.
    Crea el Pedido y el DetallePedido antes de redirigir a la pasarela,
    dejando el registro en base de datos en estado 'pendiente'.
    """
    def post(self, request, *args, **kwargs):
        producto = get_object_or_404(Producto, pk=kwargs.get("pk"))
        
        # Crear pedido pendiente
        pedido = Pedido.objects.create(
            usuario=request.user,
            estado='pendiente',
            total=producto.precio
        )
        
        DetallePedido.objects.create(
            pedido=pedido,
            producto=producto,
            precio_unitario=producto.precio,
            cantidad=1
        )
        
        # Si el producto es gratuito, confirmar pedido directamente sin pasar por Stripe
        if producto.precio <= 0:
            pedido.estado = 'completado'
            pedido.save(update_fields=['estado'])
            messages.success(request, f"¡Has obtenido «{producto.titulo}» gratis! Ya puedes descargarlo.")
            return redirect(reverse("products:showProducts") + "?compra_ok=1")
        
        try:
            base_url = request.build_absolute_uri(reverse('products:product_success'))
            success_url = f"{base_url}?pedido_id={pedido.id}&session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = request.build_absolute_uri(reverse('products:showProducts') + '?canceled=true')

            checkout_session = stripe.checkout.Session.create(
                client_reference_id=str(pedido.id),
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'eur',
                            'unit_amount': int(producto.precio * 100),
                            'product_data': {
                                'name': producto.titulo,
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            messages.error(request, f"Error al iniciar el pago: {str(e)}")
            return redirect('products:showProducts')


class ProductSuccessView(LoginRequiredMixin, View):
    """
    Vista de retorno tras un pago exitoso en Stripe para productos digitales.
    Verifica directamente la sesión con la API de Stripe para confirmar el pedido
    en base de datos sin depender del webhook.
    """
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        pedido_id = request.GET.get("pedido_id")
        session_id = request.GET.get("session_id")

        if not pedido_id or not session_id:
            messages.warning(request, "Parámetros de pago incompletos.")
            return redirect("products:showProducts")

        try:
            pedido = Pedido.objects.get(id=pedido_id, usuario=request.user)
        except Pedido.DoesNotExist:
            messages.error(request, "Pedido no encontrado.")
            return redirect("products:showProducts")

        if pedido.estado == "completado":
            titulo = pedido.detalles.first().producto.titulo if pedido.detalles.exists() else "tu producto"
            messages.success(request, f"¡Tu compra de «{titulo}» ya estaba confirmada!")
            return redirect(reverse("products:showProducts") + "?compra_ok=1")

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid" and session.get('client_reference_id') == str(pedido.id):
                pedido.estado = "completado"
                pedido.referencia_pago = session.get('payment_intent', '')
                pedido.save(update_fields=["estado", "referencia_pago"])
                
                titulo = pedido.detalles.first().producto.titulo if pedido.detalles.exists() else "tu producto"
                messages.success(
                    request,
                    f"¡Compra confirmada! Ya puedes descargar «{titulo}» desde tu perfil.",
                )
                return redirect(reverse("products:showProducts") + "?compra_ok=1")
            else:
                messages.warning(
                    request,
                    "El pago aún no está procesado. Espera unos segundos y recarga.",
                )
                return redirect("products:showProducts")
        except Exception as e:
            messages.error(request, f"Error al verificar el pago: {e}")
            return redirect("products:showProducts")


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    Webhook público para recibir notificaciones de Stripe cuando un pago es exitoso.

    Este endpoint es llamado por Stripe de forma asíncrona (de ahí el csrf_exempt).
    Distingue dos casos mediante el `client_reference_id`:
      - "reserva:<pk>" → Confirma la reserva de una clase virtual.
      - "<pk numérico>" → Confirma la compra de un producto digital.
    """
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            ref = session.get('client_reference_id', '')

            if ref and ref.startswith('reserva:'):
                # Confirmación de reserva de clase
                try:
                    reserva_id = int(ref.split('reserva:')[1])
                    reserva = Reserva.objects.get(pk=reserva_id)
                    reserva.estado = 'confirmada'
                    reserva.save(update_fields=['estado'])
                except (Reserva.DoesNotExist, ValueError, IndexError):
                    pass

            elif ref:
                # Confirmación de compra de producto digital
                try:
                    pedido = Pedido.objects.get(id=ref)
                    pedido.estado = 'completado'
                    pedido.referencia_pago = session.get('payment_intent', '')
                    pedido.save(update_fields=['estado', 'referencia_pago'])
                except (Pedido.DoesNotExist, ValueError):
                    pass

        return HttpResponse(status=200)



class DownloadProductView(LoginRequiredMixin, View):
    """
    Controlador para despachar archivos digitales de forma segura.

    Verifica que el usuario haya completado el pago, comprueba que no haya
    superado el límite de descargas del producto, y registra cada descarga
    en el modelo Descarga para trazabilidad.
    """
    def get(self, request, *args, **kwargs):
        detalle_id = kwargs.get('pk')
        detalle = get_object_or_404(DetallePedido, pk=detalle_id, pedido__usuario=request.user)
        
        if detalle.pedido.estado != 'completado':
            messages.error(request, "El pedido no está completado.")
            return redirect('home')
            
        if not Descarga.puede_descargar(detalle):
            messages.error(request, "Has excedido el límite de descargas permitidas para este producto.")
            return redirect('home')
            
        producto = detalle.producto
        if not producto.archivo_digital:
            messages.error(request, "El archivo digital no está disponible en este momento.")
            return redirect('home')
            
        # Registra la descarga con la IP real del usuario (detrás del proxy Nginx)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
            
        Descarga.objects.create(detalle=detalle, ip_origen=ip)
        
        safe_filename = os.path.basename(producto.archivo_digital.name)
        return FileResponse(producto.archivo_digital.open('rb'), as_attachment=True, filename=safe_filename)
