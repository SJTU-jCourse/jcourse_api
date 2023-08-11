from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ad.views import PromotionViewSet

router = DefaultRouter()
router.register('', PromotionViewSet, basename='promotion')

urlpatterns = [
    path('', include(router.urls)),
]
