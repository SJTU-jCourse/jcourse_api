from django.test import TestCase
from rest_framework.test import APIClient

from jcourse_api.models import *
from jcourse_api.tests import create_test_env


class CourseNotificationLevelTest(TestCase):
    def setUp(self) -> None:
        self.user1 = User.objects.create(username='test1')
        self.user2 = User.objects.create(username='test2')
        self.user3 = User.objects.create(username='test3')

        self.client1 = APIClient()
        self.user = User.objects.get(username='test1')
        self.client1.force_login(self.user)

        self.client2 = APIClient()
        self.client2.force_login(self.user2)

        create_test_env()

        dept_seiee = Department.objects.get(name='SEIEE')
        teacher_zhang = Teacher.objects.create(tid=5, name='张先生', department=dept_seiee, title='教授',
                                               pinyin='zhangfeng', abbr_pinyin='zf')
        teacher_liang = Teacher.objects.get(tid=2)

        self.course1 = Course.objects.get(code='CS2500')
        self.course2 = Course.objects.get(code='CS1500')
        self.course3 = Course.objects.get(code='MARX1001', main_teacher=teacher_liang)
        self.course4 = Course.objects.create(code='EE0501', name='电路理论', credit=4, department=dept_seiee,
                                             main_teacher=teacher_zhang)
        self.course5 = Course.objects.create(code='EE0502', name='电路实验', credit=2, department=dept_seiee,
                                             main_teacher=teacher_zhang)

        CourseNotificationLevel.objects.create(
            user=self.user,
            course=self.course1,
            notification_level=CourseNotificationLevel.NotificationLevelType.FOLLOW,
            modified_at=timezone.now() - timezone.timedelta(days=3)
        )
        CourseNotificationLevel.objects.create(
            user=self.user,
            course=self.course2,
            notification_level=CourseNotificationLevel.NotificationLevelType.IGNORE,
            modified_at=timezone.now() - timezone.timedelta(days=2)
        )
        CourseNotificationLevel.objects.create(
            user=self.user,
            course=self.course4,
            notification_level=CourseNotificationLevel.NotificationLevelType.FOLLOW,
            modified_at=timezone.now() - timezone.timedelta(days=1)
        )
        CourseNotificationLevel.objects.create(
            user=self.user,
            course=self.course5,
            notification_level=CourseNotificationLevel.NotificationLevelType.FOLLOW,
            modified_at=timezone.now()
        )

        Review.objects.create(user=self.user, course=self.course1, comment='TEST', rating=3, score='W',
                              semester=Semester.objects.get(name='2021-2022-1'))
        Review.objects.create(user=self.user, course=self.course2, comment='TEST', rating=3, score='W',
                              semester=Semester.objects.get(name='2021-2022-2'))
        Review.objects.create(user=self.user, course=self.course4, comment='TEST', rating=3, score='W',
                              semester=Semester.objects.get(name='2021-2022-2'))
        Review.objects.create(user=self.user, course=self.course5, comment='TEST', rating=3, score='W',
                              semester=Semester.objects.get(name='2021-2022-2'))

        Review.objects.create(user=self.user2, course=self.course1, comment='TEST', rating=3, score='W',
                              semester=Semester.objects.get(name='2021-2022-2'))
        Review.objects.create(user=self.user2, course=self.course4, comment='TEST', rating=3, score='W',
                              semester=Semester.objects.get(name='2021-2022-1'))

    def test_course_notification_level(self):
        my_course_notification_level = CourseNotificationLevel.objects.create(
            user=self.user,
            course=self.course3,
            notification_level=CourseNotificationLevel.NotificationLevelType.FOLLOW,
        )
        self.assertEqual(my_course_notification_level.user, self.user)
        self.assertEqual(my_course_notification_level.course, self.course3)
        self.assertEqual(my_course_notification_level.notification_level,
                         CourseNotificationLevel.NotificationLevelType.FOLLOW)

    # def test_notify_new_review_generated(self):
    #     count = Notification.objects.count()
    #     CourseNotificationLevel.objects.create(
    #         user=self.user,
    #         course=self.course3,
    #         notification_level=CourseNotificationLevel.NotificationLevelType.FOLLOW,
    #     )
    #     Review.objects.create(user=self.user, course=self.course3, comment='TEST', rating=3, score='W',
    #                           semester=Semester.objects.get(name='2021-2022-1'))
    #     self.assertEqual(Notification.objects.count(), count + 1)

    def test_course_follow_list(self):
        response = self.client1.get('/api/course/?notification_level=1').json()
        self.assertEqual(int(response['count']), 3)
        response = self.client1.get('/api/course/?notification_level=2').json()
        self.assertEqual(int(response['count']), 1)
        response = self.client1.get('/api/course/').json()
        self.assertEqual(int(response['count']), 6)
        response = self.client1.get('/api/course/?notification_level=6')
        self.assertEqual(response.status_code, 200)
        response = self.client2.get('/api/course/?notification_level=1').json()
        self.assertEqual(int(response['count']), 0)

    def test_show_course_notification_level(self):
        response = self.client1.get(f'/api/course/{self.course1.id}/').json()
        self.assertEqual(response['notification_level'], 1)
        response = self.client1.get(f'/api/course/{self.course3.id}/').json()
        self.assertEqual(response['notification_level'], None)

    def test_change_notification_level(self):
        response = self.client1.post(f'/api/course/{self.course1.id}/notification_level/', {'level': '0'}).json()
        self.assertEqual(response['notification_level'], 0)
        response = self.client1.post(f'/api/course/{self.course1.id}/notification_level/', {'level': '2'}).json()
        self.assertEqual(response['notification_level'], 2)
        response = self.client1.post(f'/api/course/{self.course1.id}/notification_level/', {'level': '4'}).json()
        self.assertEqual(response, {'error': '无效的操作类型！'})
        response = self.client1.post(f'/api/course/{self.course1.id}/notification_level/', {'read': '4'}).json()
        self.assertEqual(response, {'error': '未指定操作类型！'})
        response = self.client1.post(f'/api/course/11111/notification_level/', {'level': '0'})
        self.assertEqual(response.status_code, 404)

    def test_review_follow_list(self):
        response = self.client1.get('/api/review/?notification_level=1').json()
        self.assertEqual(int(response['count']), 5)
        response = self.client1.get('/api/review/?notification_level=2').json()
        self.assertEqual(int(response['count']), 1)
        response = self.client1.get('/api/review/').json()
        self.assertEqual(int(response['count']), 5)
        response = self.client1.get('/api/review/?notification_level=6')
        self.assertEqual(response.status_code, 200)

        response = self.client2.get('/api/review/?notification_level=1').json()
        self.assertEqual(int(response['count']), 0)
