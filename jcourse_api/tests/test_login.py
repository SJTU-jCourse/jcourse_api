from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient


class SendCodeTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.endpoint = '/oauth/email/send-code/'

    @patch('rest_framework.throttling.UserRateThrottle.allow_request')
    @patch('jcourse.throttles.EmailCodeRateThrottle.allow_request')
    def test_view(self, email_throttle, user_throttle):
        email_throttle.return_value = True
        user_throttle.return_value = True
        resp = self.client.get(self.endpoint)
        self.assertEqual(resp.status_code, 405)
        resp = self.client.post(self.endpoint, data={"email": "xxx@fdu.edu.cn"})
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(self.endpoint, data={"email": "xxx"})
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(self.endpoint)
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(self.endpoint, data={"email": "xxx@sjtu.edu.cn"})
        self.assertEqual(resp.status_code, 200)

    def test_throttle(self):
        resp = self.client.post(self.endpoint, data={"email": "xxx@sjtu.edu.cn"})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(self.endpoint, data={"email": "xxx@sjtu.edu.cn"})
        self.assertEqual(resp.status_code, 429)


class VerifyCodeTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.endpoint = '/oauth/email/verify/'

    @patch('rest_framework.throttling.UserRateThrottle.allow_request')
    @patch('jcourse.throttles.VerifyEmailRateThrottle.allow_request')
    def test_wrong_input(self, email_throttle, user_throttle):
        email_throttle.return_value = True
        user_throttle.return_value = True
        resp = self.client.post(self.endpoint, data={"code": "xxx"})
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(self.endpoint, data={"email": "xxx@sjtu.edu.cn"})
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(self.endpoint)
        self.assertEqual(resp.status_code, 400)
        resp = self.client.get(self.endpoint)
        self.assertEqual(resp.status_code, 405)

    def test_not_sent_code(self):
        resp = self.client.post(self.endpoint, data={"email": "xxx@sjtu.edu.cn", "code": "123456"})
        self.assertEqual(resp.status_code, 400)

    @patch('rest_framework.throttling.UserRateThrottle.allow_request')
    @patch('jcourse.throttles.VerifyEmailRateThrottle.allow_request')
    def test_valid(self, email_throttle, user_throttle):
        email_throttle.return_value = True
        user_throttle.return_value = True
        email = "xxx@sjtu.edu.cn"
        resp = self.client.post('/oauth/email/send-code/', data={"email": email})
        self.assertEqual(resp.status_code, 200)
        code = cache.get(email)
        self.assertIsNotNone(code)
        resp = self.client.post(self.endpoint, data={"email": email, "code": code})
        self.assertEqual(resp.status_code, 200)
