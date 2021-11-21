from django.test import TestCase
from rest_framework.test import APIClient

from jcourse_api.tests import *
from jcourse_api.views import get_user_point


class UserTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        create_review()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)

    def test_me(self):
        response = self.client.get('/api/me/').json()
        self.assertIn('id', response)
        self.assertEqual(response['username'], 'test')
        self.assertEqual(response['is_staff'], False)

    def test_points(self):
        result = get_user_point(self.user)
        self.assertEqual(result['points'], 6)


class EnrollLessonTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.review = create_review()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/lesson/'
        courses = Course.objects.all()
        for course in courses:
            EnrollCourse.objects.create(user=self.user, course=course, semester=Semester.objects.first())

    def test_list(self):
        response = self.client.get(self.endpoint).json()
        self.assertEqual(len(response), 4)
        for course in response:
            self.assertEqual(course['semester']['name'], '2021-2022-3')

    def test_course_list_status(self):
        response = self.client.get(f'/api/course/').json()
        for course in response['results']:
            self.assertEqual(course['semester']['name'], '2021-2022-3')

    def test_course_detail_status(self):
        response = self.client.get(f'/api/course/{Course.objects.first().id}/').json()
        self.assertEqual(response['semester']['name'], '2021-2022-3')

    def test_course_in_review_status(self):
        response = self.client.get(f'/api/course-in-review/', {'q': 'cs'}).json()
        for course in response:
            self.assertEqual(course['semester']['name'], '2021-2022-3')


class ReportTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/report/'

    def test_missing_argument(self):
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, 400)
        self.assertIn('comment', response.json())

    def test_create(self):
        response = self.client.post(self.endpoint, {'comment': 'TEST'}).json()
        self.assertEqual(response['id'], 1)
        self.assertEqual(response['comment'], 'TEST')
        self.assertIn('created', response)
        self.assertIn('reply', response)
        self.assertEqual(response['user'], self.user.id)

    def test_list(self):
        self.client.post(self.endpoint, {'comment': 'TEST'})
        response = self.client.get(self.endpoint).json()
        self.assertEqual(len(response), 1)
