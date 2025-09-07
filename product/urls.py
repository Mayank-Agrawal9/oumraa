from django.urls import path, include
from rest_framework import routers

from product.views import *

router = routers.DefaultRouter()
router.register(r'wishlist', WishListViewSet, basename='wishlist')
router.register(r'order-item', OrderItemViewSet, basename='order-items')
router.register(r'review-product', ReviewProductViewSet, basename='review-product')


urlpatterns = [
    path('', include(router.urls)),
]