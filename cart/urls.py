

from django.urls import path
from cart.views import CartView, CartItemDetailView, CartSyncView

urlpatterns = [
    path('', CartView.as_view(), name='cart'),
    path('sync/', CartSyncView.as_view(), name='cart_sync'),
    path('<str:cart_item_id>/', CartItemDetailView.as_view(), name='cart_item_detail'),
]