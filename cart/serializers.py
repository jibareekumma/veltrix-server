

from rest_framework import serializers
from cart.models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    cartItemId = serializers.CharField(source='cart_item_id')
    id = serializers.CharField(source='product_id')

    class Meta:
        model = CartItem
        fields = ('cartItemId', 'id', 'title', 'price', 'image', 'size', 'color', 'quantity')