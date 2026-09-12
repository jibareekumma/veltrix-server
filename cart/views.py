

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from cart.models import CartItem
from cart.serializers import CartItemSerializer


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_item_id = serializer.validated_data['cart_item_id']

        item, created = CartItem.objects.get_or_create(
            user=request.user,
            cart_item_id=cart_item_id,
            defaults=serializer.validated_data,
        )

        if not created:
            item.quantity += serializer.validated_data.get('quantity', 1)
            item.save()

        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, cart_item_id):
        try:
            item = CartItem.objects.get(user=request.user, cart_item_id=cart_item_id)
        except CartItem.DoesNotExist:
            return Response({'detail': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

        quantity = request.data.get('quantity')
        if quantity is not None:
            item.quantity = quantity
            item.save()

        return Response(CartItemSerializer(item).data)

    def delete(self, request, cart_item_id):
        try:
            item = CartItem.objects.get(user=request.user, cart_item_id=cart_item_id)
        except CartItem.DoesNotExist:
            return Response({'detail': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        local_items = request.data.get('items', [])

        for item_data in local_items:
            serializer = CartItemSerializer(data=item_data)
            serializer.is_valid(raise_exception=True)
            cart_item_id = serializer.validated_data['cart_item_id']

            existing = CartItem.objects.filter(user=request.user, cart_item_id=cart_item_id).first()
            if existing:
                existing.quantity += serializer.validated_data.get('quantity', 1)
                existing.save()
            else:
                CartItem.objects.create(user=request.user, **serializer.validated_data)

        items = CartItem.objects.filter(user=request.user)
        return Response(CartItemSerializer(items, many=True).data)