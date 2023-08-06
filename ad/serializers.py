from rest_framework import serializers

from ad.models import Promotion


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = ('id', 'touchpoint', 'image', 'text', 'jump_link')
