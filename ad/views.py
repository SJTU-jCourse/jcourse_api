from rest_framework import viewsets

from ad.repository import get_promotions
from ad.serializers import PromotionSerializer


# Create your views here.
class PromotionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = get_promotions()
    serializer_class = PromotionSerializer
    pagination_class = None
