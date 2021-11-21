from django.test import TestCase
from rest_framework.test import APIClient

from jcourse_api.tests import *


class NoticeTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(username='test')
        self.client.force_login(self.user)
        Notice.objects.create(title='TEST1', message='Just a test notice', available=True)
        Notice.objects.create(title='TEST2', message='Just a test notice', available=False)

    def test_list(self):
        response = self.client.get('/api/notice/').json()
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['title'], 'TEST1')
        self.assertEqual(response[0]['message'], 'Just a test notice')


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
