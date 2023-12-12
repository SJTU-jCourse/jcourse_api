import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from jcourse_api.tests import *
from oauth.utils import hash_username


class AnnouncementTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(username='test')
        self.client.force_login(self.user)
        Announcement.objects.create(title='TEST3', message='Just a test notice',
                                    created_at=timezone.now() - datetime.timedelta(days=1),
                                    available=True)
        Announcement.objects.create(title='TEST1', message='Just a test notice',
                                    created_at=timezone.now(),
                                    available=True,
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
        self.assertEqual(response['course_count'], 4)
        self.assertEqual(response['user_count'], 1)
        self.assertEqual(response['review_count'], 1)
        self.assertEqual(response['course_with_review_count'], 1)
        self.assertEqual(response['course_review_count_dist'], [{"value": 1, "count": 1}])
        self.assertEqual(response['course_review_avg_dist'], [{"value": 3.0, "count": 1}])
        self.assertEqual(response['review_rating_dist'], [{"value": 3, "count": 1}])
        self.assertIsNotNone(response['user_join_time'])
        self.assertIsNotNone(response['review_create_time'])


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
        self.assertEqual(response['points'], 0)

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


class CommonInfoTestCase(TestCase):

    def setUp(self) -> None:
        create_test_env()
        create_review()
        self.client = APIClient()
        self.endpoint = '/api/common/'
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)

        self.announcement = Announcement.objects.create(title='TEST3', message='Just a test notice',
                                                        created_at=timezone.now(),
                                                        available=True)
        self.semester = Semester.objects.first()
        self.course = Course.objects.first()
        self.enroll = EnrollCourse.objects.create(course=self.course, semester=self.semester, user=self.user)
        self.review = Review.objects.get(user=self.user)

    def test_request_body(self):
        resp = self.client.get(self.endpoint).json()
        self.assertEqual(resp["user"],
                         {"id": self.user.id, "username": self.user.username, "is_staff": self.user.is_staff})
        self.assertEqual(len(resp["announcements"]), 1)
        self.assertEqual(len(resp["semesters"]), 4)
        self.assertEqual(len(resp["enrolled_courses"]), 1)
        self.assertEqual(resp["enrolled_courses"][0], {"semester_id": self.semester.id, "course_id": self.course.id})
        self.assertEqual(resp["my_reviews"][0],
                         {"semester_id": self.review.semester_id, "course_id": self.review.course_id,
                          "id": self.review.id})
