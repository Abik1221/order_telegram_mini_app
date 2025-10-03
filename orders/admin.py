# orders/admin.py
from django.contrib import admin
from .models import BurgerType, Order, OrderItem
from django.utils import timezone
from django.conf import settings
import requests

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.action(description='Mark selected orders as cooked (notify user)')
def mark_cooked(modeladmin, request, queryset):
    for order in queryset:
        if order.status != 'cooked':
            order.status = 'cooked'
            order.actual_ready_at = timezone.now()
            order.save()
            # send notification
            if order.telegram_user_id:
                url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
                text = f"🍔 Your order #{order.id} is ready! (Marked by admin)."
                try:
                    requests.post(url, json={"chat_id": order.telegram_user_id, "text": text})
                except:
                    pass

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','full_name','phone','status','created_at','estimated_ready_at')
    inlines = [OrderItemInline]
    actions = [mark_cooked]

@admin.register(BurgerType)
class BurgerTypeAdmin(admin.ModelAdmin):
    list_display = ('name','price','prep_time_estimate')
