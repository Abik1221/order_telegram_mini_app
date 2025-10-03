# orders/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings

class BurgerType(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='burger_images/', null=True, blank=True)
    # Estimated preparation time in minutes (initial default, updated from history)
    prep_time_estimate = models.PositiveIntegerField(default=8)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cooked', 'Cooked / Ready'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    ]

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    telegram_user_id = models.BigIntegerField(null=True, blank=True)  # from Web App
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    estimated_ready_at = models.DateTimeField(null=True, blank=True)
    # actual_ready_at filled when admin marks as cooked
    actual_ready_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def total_price(self):
        return sum([item.subtotal() for item in self.items.all()])

    def __str__(self):
        return f"Order #{self.id} - {self.full_name} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    burger = models.ForeignKey(BurgerType, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    special = models.BooleanField(default=False)  # e.g., 'spacial' in your example

    def subtotal(self):
        return self.burger.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.burger.name}"
