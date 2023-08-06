from rest_framework import viewsets

from ad.models import Promotion
from ad.serializers import PromotionSerializer


# Create your views here.
class PromotionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Promotion.objects.filter(available=True)
    serializer_class = PromotionSerializer
    pagination_class = None
