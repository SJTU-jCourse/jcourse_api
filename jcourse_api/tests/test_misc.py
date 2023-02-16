from django.test import TestCase
from rest_framework.test import APIClient

from jcourse_api.tests import *
from oauth.utils import hash_username


class AnnouncementTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(username='test')
        self.client.force_login(self.user)
        Announcement.objects.create(title='TEST3', message='Just a test notice', available=True)
        Announcement.objects.create(title='TEST1', message='Just a test notice', available=True,
                                    url='https://example.com')
        Announcement.objects.create(title='TEST2', message='Just a test notice', available=False)

    def test_list(self):
        response = self.client.get('/api/announcement/').json()
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]['title'], 'TEST1')
        self.assertEqual(response[0]['message'], 'Just a test notice')
        self.assertEqual(response[0]['url'], 'https://example.com')
        self.assertEqual(response[1]['url'], None)
        self.assertEqual(response[1]['title'], 'TEST3')


class StatisticTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        create_review()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)

    def test_get(self):
        response = self.client.get('/api/statistic/').json()
        self.assertEqual(response['courses'], 4)
        self.assertEqual(response['users'], 1)
        self.assertEqual(response['reviews'], 1)
        self.assertEqual(response['courses_with_review'], 1)


class ApiKeyTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        create_review()
        self.client = APIClient()
        self.endpoint = '/api/points/'
        user = User.objects.get(username='test')
        user.username = hash_username('test')
        user.save()
        self.apikey = ApiKey.objects.create(key='123456', description='TEST')

    def test_normal(self):
        data = {'account': 'test'}
        response = self.client.post(self.endpoint, data, HTTP_API_KEY="123456").json()
        self.assertEqual(response['points'], 4)
        self.assertEqual(response['reviews'], 1)
        self.assertEqual(response['first_reviews'], 1)
        self.assertEqual(response['approves'], 1)
        self.assertEqual(response['first_reviews_approves'], 1)

    def test_wrong_apikey(self):
        data = {'account': 'test'}
        response = self.client.post(self.endpoint, data, HTTP_API_KEY="123457")
        self.assertEqual(response.status_code, 400)

    def test_wrong_account(self):
        data = {'account': 'test2'}
        response = self.client.post(self.endpoint, data, HTTP_API_KEY="123457")
        self.assertEqual(response.status_code, 400)

    def test_blocked_user(self):
        user = User.objects.get(username=hash_username('test'))
        user.is_active = False
        user.save()
        data = {'account': 'test'}
        response = self.client.post(self.endpoint, data, HTTP_API_KEY="123457")
        self.assertEqual(response.status_code, 400)
