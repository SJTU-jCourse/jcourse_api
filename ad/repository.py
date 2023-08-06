from ad.models import Promotion


def get_promotions():
    return Promotion.objects.filter(available=True)
