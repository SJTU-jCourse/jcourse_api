from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from ad.models import Promotion


class PromotionTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(username='test')
        self.promotion = Promotion.objects.create()
        self.client.force_login(self.user)

    def test_click(self):
        resp = self.client.post(f'/api/promotion/{self.promotion.id}/click/')
        self.assertEqual(resp.status_code, 200)
        self.promotion.refresh_from_db()
        self.assertEqual(self.promotion.click_times, 1)
