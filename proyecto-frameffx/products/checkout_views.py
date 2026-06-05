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
    Vista que inicializa la sesión de pago con Stripe para un producto digital.
    Aquí construyo el Pedido y el DetallePedido antes de saltar a la pasarela,
    para dejar el rastro en base de datos en estado 'pendiente'.
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
        
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=pedido.id,
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
                success_url=request.build_absolute_uri(reverse('home') + '?success=true'),
                cancel_url=request.build_absolute_uri(reverse('home') + '?canceled=true'),
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            messages.error(request, f"Error al iniciar el pago: {str(e)}")
            return redirect('products:showProducts')


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    Webhook público para recibir la notificación de Stripe cuando un pago es exitoso.

    He configurado este endpoint para que Stripe lo llame asíncronamente (de ahí el csrf_exempt).
    Lo he programado para distinguir dos casos mediante el `client_reference_id`:
      - "reserva:<pk>" → Confirmo la reserva de una clase virtual.
      - "<pk numérico>" → Confirmo la compra de un producto digital.
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
                # ── Confirmación de reserva de clase ──────────────────────
                try:
                    reserva_id = int(ref.split('reserva:')[1])
                    reserva = Reserva.objects.get(pk=reserva_id)
                    reserva.estado = 'confirmada'
                    reserva.save(update_fields=['estado'])
                except (Reserva.DoesNotExist, ValueError, IndexError):
                    pass

            elif ref:
                # ── Confirmación de compra de producto digital ─────────────
                try:
                    pedido = Pedido.objects.get(id=ref)
                    pedido.estado = 'completado'
                    pedido.referencia_pago = session.get('payment_intent', '')
                    pedido.save(update_fields=['estado', 'referencia_pago'])
                except Pedido.DoesNotExist:
                    pass

        return HttpResponse(status=200)



class DownloadProductView(LoginRequiredMixin, View):
    """
    Controlador para despachar archivos digitales de forma segura.
    
    En esta vista me aseguro de que el usuario haya pagado realmente,
    compruebo que no haya excedido el límite de descargas del producto,
    y registro cada bajada usando el modelo `Descarga` por seguridad.
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
            
        # Registrar la descarga
        ip = request.META.get('REMOTE_ADDR')
        Descarga.objects.create(detalle=detalle, ip_origen=ip)
        
        return FileResponse(producto.archivo_digital.open('rb'), as_attachment=True, filename=producto.archivo_digital.name)
