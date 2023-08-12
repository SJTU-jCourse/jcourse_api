from rest_framework import serializers

from ad.models import Promotion


class PromotionSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = ('id', 'touchpoint', 'image', 'text', 'jump_link')

    def get_image(self, obj: Promotion):
        if obj.external_image is not None and obj.external_image != "":
            return obj.external_image
        return obj.image.url
