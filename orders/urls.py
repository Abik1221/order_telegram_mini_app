# orders/urls.py
from django.urls import path
from .views import BurgerTypeListCreate, OrderCreateView, AdminOrderList, AdminMarkReadyView

urlpatterns = [
    path('burgers/', BurgerTypeListCreate.as_view(), name='burger-list-create'),
    path('orders/create/', OrderCreateView.as_view(), name='order-create'),
    path('admin/orders/', AdminOrderList.as_view(), name='admin-orders'),
    path('admin/orders/<int:pk>/mark_ready/', AdminMarkReadyView.as_view(), name='admin-order-mark-ready'),
]
