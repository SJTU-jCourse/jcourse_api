from django.db.models import F
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ad.models import Promotion
from ad.repository import get_promotions
from ad.serializers import PromotionSerializer


# Create your views here.
class PromotionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = get_promotions()
    serializer_class = PromotionSerializer
    pagination_class = None

    @action(detail=True, methods=['POST'])
    def click(self, request, pk=None):
        promotion = Promotion.objects.get(pk=pk)
        promotion.click_times = F('click_times') + 1
        promotion.save(update_fields=['click_times'])
        data = PromotionSerializer(many=False).data
        return Response(data)
