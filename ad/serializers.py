from rest_framework import serializers

from ad.models import Promotion


class PromotionSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = ('id', 'touchpoint', 'image', 'text', 'jump_link')

    def get_image(self, obj: Promotion):
        return obj.image.url
