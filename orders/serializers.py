from rest_framework import serializers
from django.utils import timezone
from .models import BurgerType, Order, OrderItem


class BurgerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BurgerType
        fields = [
            'id',
            'name',
            'description',
            'price',
            'image',
            'prep_time_estimate',
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    burger_detail = BurgerTypeSerializer(source='burger', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'burger', 'burger_detail', 'quantity', 'special']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'full_name',
            'phone',
            'telegram_user_id',
            'created_at',
            'status',
            'estimated_ready_at',
            'actual_ready_at',
            'notes',
            'items',
            'total_price',
        ]

    def get_total_price(self, obj: Order):
        return float(obj.total_price()) if hasattr(obj, 'items') else 0.0


class OrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['burger', 'quantity', 'special']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'full_name', 'phone', 'telegram_user_id', 'notes', 'items', 'estimated_ready_at']
        read_only_fields = ['id', 'estimated_ready_at']

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('At least one item is required')
        for it in value:
            if it.get('quantity', 0) <= 0:
                raise serializers.ValidationError('Quantity must be greater than zero')
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        # naive ETA: max prep_time_estimate among ordered burgers + small queue buffer
        max_minutes = 0
        for item in items_data:
            burger: BurgerType = item['burger']
            max_minutes = max(max_minutes, burger.prep_time_estimate)

        # Optional simple queue buffer based on total qty
        total_qty = sum(it['quantity'] for it in items_data)
        buffer_minutes = 2 if total_qty <= 2 else 5
        eta = timezone.now() + timezone.timedelta(minutes=max_minutes + buffer_minutes)
        order.estimated_ready_at = eta
        order.save()

        OrderItem.objects.bulk_create([
            OrderItem(order=order, **item) for item in items_data
        ])

        return order


