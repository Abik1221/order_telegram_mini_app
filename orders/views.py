# orders/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import BurgerType, Order
from .serializers import BurgerTypeSerializer, OrderCreateSerializer, OrderSerializer
from django.shortcuts import get_object_or_404
from django.conf import settings
import requests
from django.utils import timezone

BOT_API_URL = "https://api.telegram.org/bot" + settings.BOT_TOKEN

class BurgerTypeListCreate(generics.ListCreateAPIView):
    queryset = BurgerType.objects.all()
    serializer_class = BurgerTypeSerializer
    permission_classes = [permissions.AllowAny]  # You can restrict create to staff later

class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        order = serializer.save()
        # send confirmation message to user via bot if we have telegram_user_id
        if order.telegram_user_id:
            text = f"✅ Order received — #{order.id}\nEstimated ready at: {order.estimated_ready_at.strftime('%Y-%m-%d %H:%M')}\nTotal: {order.total_price():.2f}"
            send_to_telegram(order.telegram_user_id, text)

def send_to_telegram(chat_id, text):
    try:
        url = f"{BOT_API_URL}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": text})
        return resp.ok
    except Exception as e:
        return False

class AdminOrderList(generics.ListAPIView):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminMarkReadyView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status == 'cooked':
            return Response({"detail":"Already marked cooked"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'cooked'
        order.actual_ready_at = timezone.now()
        order.save()
        # Update burger prep_time_estimate from history:
        update_prep_estimates(order)
        # Notify user via bot
        if order.telegram_user_id:
            text = f"🍔 Your order #{order.id} is ready! Please collect it. (Marked ready at {order.actual_ready_at.strftime('%Y-%m-%d %H:%M')})"
            send_to_telegram(order.telegram_user_id, text)
        return Response(OrderSerializer(order).data)

def update_prep_estimates(order):
    # For each item, compute the actual prep time for this order and adjust burger prep_time_estimate
    if not order.actual_ready_at:
        return
    actual_minutes = int((order.actual_ready_at - order.created_at).total_seconds() / 60)
    # distribute actual minutes proportionally to items quantities as a simple approach
    total_qty = sum(item.quantity for item in order.items.all())
    if total_qty == 0:
        return
    for item in order.items.all():
        burger = item.burger
        # observed per-burger minutes
        observed = max(1, round(actual_minutes * (item.quantity / total_qty)))
        # simple moving average: new_est = (old_est*3 + observed)/4
        burger.prep_time_estimate = int(round((burger.prep_time_estimate * 3 + observed) / 4.0))
        burger.save()
