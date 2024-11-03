import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from jcourse_api.models import *


class NotificationTest(TestCase):
    def create_env(self):
        report = Report.objects.create(user=self.user, comment='test', created_at=timezone.now())
        self.notification1 = Notification.objects.create(recipient=self.user2,
                                                         type=7,
                                                         content_type=ContentType.objects.get_for_model(report),
                                                         object_id=report.id,
                                                         created_at=timezone.now() - datetime.timedelta(days=1)
                                                         )
        self.notification2 = Notification.objects.create(recipient=self.user,
                                                         type=1,
                                                         created_at=timezone.now() - datetime.timedelta(days=2)
                                                         )
        self.notification3 = Notification.objects.create(recipient=self.user,
                                                         type=1,
                                                         public=False,
                                                         read_at=timezone.now() - datetime.timedelta(hours=3),
                                                         created_at=timezone.now() - datetime.timedelta(hours=4)
                                                         )
        self.notification4 = Notification.objects.create(recipient=self.user,
                                                         type=2,
                                                         content_type=ContentType.objects.get_for_model(report),
                                                         object_id=report.id,
                                                         read_at=timezone.now(),
                                                         created_at=timezone.now() - datetime.timedelta(hours=2)
                                                         )

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(username='test4')
        self.user2 = User.objects.create(username='test5')
        self.client.force_login(self.user)
        self.endpoint = '/api/notification/'

    def test_report_replied_notification(self):
        """
        Test if notification is created_at when a report is replied.
        """
        from jcourse_api.models import Report
        report = Report.objects.create(user=self.user, comment='test', created_at=timezone.now())
        self.assertEqual(Notification.objects.count(), 0)
        report.reply = 'TEST'
        report.save()
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.type, 7)
        self.assertEqual(notification.read_at, None)

    def test_user_notification_list_empty(self):
        response = self.client.get(self.endpoint).json()
        self.assertEqual(len(response['results']), 0)

    def test_not_authed_user_notification_list(self):
        self.create_env()
        client = APIClient()
        user8 = User.objects.create(username='test8')
        client.force_login(user8)
        response = client.get(self.endpoint).json()
        self.assertEqual(len(response['results']), 0)

    def test_user_notification_list(self):
        self.create_env()
        response = self.client.get(self.endpoint).json()
        self.assertEqual(len(response['results']), 2)

    def test_user_change_notification_read_or_unread(self):
        self.create_env()
        response1 = self.client.post(f'{self.endpoint}{self.notification2.id}/read/', {'read': '1'}).json()
        self.assertIsNotNone(response1['read_at'])
        notification1 = Notification.objects.get(id=self.notification2.id)
        self.assertIsNotNone(notification1.read_at)
        response2 = self.client.post(f'{self.endpoint}{self.notification2.id}/read/', {'read': '0'}).json()
        self.assertIsNone(response2['read_at'])
        notification2 = Notification.objects.get(id=self.notification2.id)
        self.assertIsNone(notification2.read_at)
        response = self.client.post(f'{self.endpoint}{1111}/read/', {'read': '0'})
        self.assertEqual(response.status_code, 404)
        response = self.client.post(f'{self.endpoint}{self.notification2.id}/read/', {'find': '0'}).json()
        self.assertEqual(response, {'error': '未指定操作类型！'})

    def test_not_authed_user_change_read_state(self):
        self.create_env()
        client = APIClient()
        user8 = User.objects.create(username='test8')
        client.force_login(user8)
        response = client.post(f'{self.endpoint}{self.notification2.id}/read/', {'read': '1'})
        self.assertEqual(response.status_code, 404)
