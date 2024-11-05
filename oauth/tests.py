from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from oauth.models import UserProfile
from oauth.utils import hash_username, get_or_create_user, auth_get_email_code, reset_get_email_code
from utils.common import get_time_now


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
        self.assertEqual(resp.json(), {'detail': '用户名或密码错误。'})

    def test_logout(self):
        resp = self.client.post('/oauth/logout/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'detail': '已登出。'})


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
        resp = self.client.post(self.endpoint)
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(self.endpoint, data={"account": "xxx"})
        self.assertEqual(resp.status_code, 200)
        # self.assertEqual(len(mail.outbox), 1)
        # self.assertEqual(mail.outbox[0].subject, '选课社区验证码')

    def test_throttle(self):
        resp = self.client.post(self.endpoint, data={"account": "xxx@sjtu.edu.cn"})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(self.endpoint, data={"account": "xxx@sjtu.edu.cn"})
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
        resp = self.client.post(self.endpoint, data={"account": "xxx@sjtu.edu.cn"})
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(self.endpoint)
        self.assertEqual(resp.status_code, 400)
        resp = self.client.get(self.endpoint)
        self.assertEqual(resp.status_code, 405)

    def test_not_sent_code(self):
        resp = self.client.post(self.endpoint, data={"account": "xxx@sjtu.edu.cn", "code": "123456"})
        self.assertEqual(resp.status_code, 400)

    @patch('rest_framework.throttling.UserRateThrottle.allow_request')
    @patch('jcourse.throttles.VerifyAuthRateThrottle.allow_request')
    def test_max_tries(self, email_throttle, user_throttle):
        email_throttle.return_value = True
        user_throttle.return_value = True
        account = "xxx"
        resp = self.client.post('/oauth/email/send-code/', data={"account": account})
        self.assertEqual(resp.status_code, 200)
        # 1st try
        resp = self.client.post(self.endpoint, data={"account": account, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 2nd try
        resp = self.client.post(self.endpoint, data={"account": account, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 3rd try
        resp = self.client.post(self.endpoint, data={"account": account, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 4th try
        resp = self.client.post(self.endpoint, data={"account": account, "code": "123456"})
        self.assertEqual(resp.status_code, 429)
        # 没有申请过
        account = "xxx2"
        # 1st try
        resp = self.client.post(self.endpoint, data={"account": account, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 2nd try
        resp = self.client.post(self.endpoint, data={"account": account, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 3rd try
        resp = self.client.post(self.endpoint, data={"account": account, "code": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 4th try
        resp = self.client.post(self.endpoint, data={"account": account, "code": "123456"})
        self.assertEqual(resp.status_code, 429)

    @patch('rest_framework.throttling.UserRateThrottle.allow_request')
    @patch('jcourse.throttles.VerifyAuthRateThrottle.allow_request')
    def test_valid(self, email_throttle, user_throttle):
        email_throttle.return_value = True
        user_throttle.return_value = True
        email = "xxx@sjtu.edu.cn"
        resp = self.client.post('/oauth/email/send-code/', data={"account": email})
        self.assertEqual(resp.status_code, 200)
        # self.assertEqual(len(mail.outbox), 1)
        # self.assertEqual(mail.outbox[0].subject, '选课社区验证码')
        code = auth_get_email_code(email)
        self.assertIsNotNone(code)
        resp = self.client.post(self.endpoint, data={"account": email, "code": code})
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
        self.username = "example"
        self.password = "test"
        username = hash_username(self.username)
        self.user = User.objects.create_user(username=username, password=self.password)
        self.client = APIClient()
        self.endpoint = '/oauth/email/login/'
        cache.clear()

    def test_valid(self):
        resp = self.client.post(self.endpoint, data={"account": self.username, "password": self.password})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["account"], "example")

    def test_wrong_password(self):
        resp = self.client.post(self.endpoint, data={"account": self.username, "password": "123456"})
        self.assertEqual(resp.status_code, 400)

    @patch('rest_framework.throttling.UserRateThrottle.allow_request')
    @patch('jcourse.throttles.VerifyAuthRateThrottle.allow_request')
    def test_throttle(self, email_throttle, user_throttle):
        email_throttle.return_value = True
        user_throttle.return_value = True
        # 1st try
        resp = self.client.post(self.endpoint, data={"account": self.username, "password": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 2nd try
        resp = self.client.post(self.endpoint, data={"account": self.username, "password": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 3rd try
        resp = self.client.post(self.endpoint, data={"account": self.username, "password": "123456"})
        self.assertEqual(resp.status_code, 400)
        # 4th try
        resp = self.client.post(self.endpoint, data={"account": self.username, "password": "123456"})
        self.assertEqual(resp.status_code, 429)


class ResetPasswordTest(TestCase):
    def setUp(self) -> None:
        self.username = "test"
        self.user = User.objects.create_user(username=hash_username(self.username))
        self.client = APIClient()
        self.client.force_login(self.user)
        self.password = "new-password"
        cache.clear()

    @patch('jcourse.throttles.EmailCodeRateThrottle.allow_request')
    def test_wrong_input(self, email_throttle):
        email_throttle.return_value = True
        resp = self.client.post("/oauth/reset-password/send-code/")
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post("/oauth/reset-password/send-code/", data={"account": "xxx@example.com"})
        self.assertEqual(resp.status_code, 400)

    @patch('jcourse.throttles.EmailCodeRateThrottle.allow_request')
    def test_send_code(self, email_throttle):
        email_throttle.return_value = True
        resp = self.client.post("/oauth/reset-password/send-code/", data={"account": self.username})
        self.assertEqual(resp.status_code, 200)
        # self.assertEqual(len(mail.outbox), 1)
        # self.assertEqual(mail.outbox[0].subject, '选课社区验证码')

    def test_input_case(self):
        resp = self.client.post("/oauth/reset-password/send-code/", data={"account": self.username.upper()})
        self.assertEqual(resp.status_code, 200)

    def test_reset(self):
        self.client.post("/oauth/reset-password/send-code/", data={"account": self.username})
        code = reset_get_email_code(self.username)

        resp = self.client.post("/oauth/reset-password/reset/",
                                data={"account": self.username, "code": code, "password": self.password})
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))

    def test_login_after_reset(self):
        self.test_reset()
        client2 = APIClient()
        resp = client2.post("/oauth/email/login/", data={"account": self.username, "password": self.password})
        self.assertEqual(resp.status_code, 200)


class UserProfileTestCase(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test1')
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)

    def test_auto_ban(self):
        self.user_profile.suspended_till = get_time_now()
        self.user_profile.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.is_active, False)

    def test_auto_release(self):
        self.user.is_active = False
        self.user.save()
        self.user_profile.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.is_active, True)

