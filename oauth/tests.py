from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from oauth.utils import hash_username, get_or_create_user, get_email_code


class LoginTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        user = User.objects.create_user(username="test", password="pass")
        user.save()

    def test_login(self):
        resp = self.client.post('/oauth/login/', data={"username": "test", "password": "pass"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"account": "test"})

    def test_wrong_login(self):
        resp = self.client.post('/oauth/login/', data={"username": "test", "password": "pass1"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json(), {'detail': '参数错误'})

    def test_logout(self):
        resp = self.client.post('/oauth/logout/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'detail': 'logged out'})


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
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '选课社区验证码')

    def test_throttle(self):
        resp = self.client.post(self.endpoint, data={"email": "xxx@sjtu.edu.cn"})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(self.endpoint, data={"email": "xxx@sjtu.edu.cn"})
        self.assertEqual(resp.status_code, 429)


class VerifyCodeTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.endpoint = '/oauth/email/verify/'
        cache.clear()

    @patch('rest_framework.throttling.UserRateThrottle.allow_request')
    @patch('jcourse.throttles.VerifyAuthRateThrottle.allow_request')
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
    @patch('jcourse.throttles.VerifyAuthRateThrottle.allow_request')
    def test_max_tries(self, email_throttle, user_throttle):
        email_throttle.return_value = True
        user_throttle.return_value = True
        email = "xxx@sjtu.edu.cn"
        resp = self.client.post('/oauth/email/send-code/', data={"email": email})
        self.assertEqual(resp.status_code, 200)
        # 1st try
        resp = self.client.post(self.endpoint, data={"email": email, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 2nd try
        resp = self.client.post(self.endpoint, data={"email": email, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 3rd try
        resp = self.client.post(self.endpoint, data={"email": email, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 4th try
        resp = self.client.post(self.endpoint, data={"email": email, "code": "123456"})
        self.assertEqual(resp.status_code, 429)
        # 没有申请过
        email = "xxx2@sjtu.edu.cn"
        # 1st try
        resp = self.client.post(self.endpoint, data={"email": email, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 2nd try
        resp = self.client.post(self.endpoint, data={"email": email, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 3rd try
        resp = self.client.post(self.endpoint, data={"email": email, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 4th try
        resp = self.client.post(self.endpoint, data={"email": email, "code": "123456"})
        self.assertEqual(resp.status_code, 429)

    @patch('rest_framework.throttling.UserRateThrottle.allow_request')
    @patch('jcourse.throttles.VerifyAuthRateThrottle.allow_request')
    def test_valid(self, email_throttle, user_throttle):
        email_throttle.return_value = True
        user_throttle.return_value = True
        email = "xxx@sjtu.edu.cn"
        resp = self.client.post('/oauth/email/send-code/', data={"email": email})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '选课社区验证码')
        code = get_email_code(email)
        self.assertIsNotNone(code)
        resp = self.client.post(self.endpoint, data={"email": email, "code": code})
        self.assertEqual(resp.status_code, 200)


class GetOrCreateUserTest(TestCase):
    def test_lower_first_upper_last(self):
        username = hash_username("abc")

        get_or_create_user("abc")
        user = User.objects.get()
        self.assertEqual(user.username, username)

        get_or_create_user("Abc")
        user = User.objects.get()
        self.assertEqual(user.username, username)

    def test_exactly_the_same_lower(self):
        username = hash_username("abc")

        get_or_create_user("abc")
        user = User.objects.get()
        self.assertEqual(user.username, username)

        get_or_create_user("abc")
        user = User.objects.get()
        self.assertEqual(user.username, username)

    def test_exactly_the_same_upper(self):
        User.objects.create(username=hash_username("Abc"))
        username = hash_username("abc")
        get_or_create_user("Abc")
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.username, username)

    def test_upper_first_low_last(self):
        User.objects.create(username=hash_username("Abc"))
        get_or_create_user("abc")
        get_or_create_user("Abc")
        self.assertEqual(User.objects.count(), 2)


class EmailPasswordLoginTest(TestCase):
    def setUp(self) -> None:
        self.email = "example@example.com"
        self.password = "test"
        username = hash_username(self.email)
        self.user = User.objects.create_user(username=username, password=self.password)
        self.client = APIClient()
        self.endpoint = '/oauth/email/login/'
        cache.clear()

    def test_valid(self):
        resp = self.client.post(self.endpoint, data={"email": self.email, "password": self.password})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["account"], "example")

    def test_wrong_password(self):
        resp = self.client.post(self.endpoint, data={"email": self.email, "password": "123456"})
        self.assertEqual(resp.status_code, 400)

    @patch('rest_framework.throttling.UserRateThrottle.allow_request')
    @patch('jcourse.throttles.VerifyAuthRateThrottle.allow_request')
    def test_throttle(self, email_throttle, user_throttle):
        email_throttle.return_value = True
        user_throttle.return_value = True
        # 1st try
        resp = self.client.post(self.endpoint, data={"email": self.email, "password": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 2nd try
        resp = self.client.post(self.endpoint, data={"email": self.email, "password": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 3rd try
        resp = self.client.post(self.endpoint, data={"email": self.email, "password": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 4th try
        resp = self.client.post(self.endpoint, data={"email": self.email, "password": "123456"})
        self.assertEqual(resp.status_code, 429)
