from django.test import TestCase
from rest_framework.test import APIClient

from jcourse_api.tests import *


class ReviewTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.review = create_review()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/review/'

    def test_list(self):
        response = self.client.get(self.endpoint).json()
        self.assertEqual(response['count'], 1)
        review = response['results'][0]
        self.assertEqual(review['semester'], '2021-2022-1')
        course = review['course']
        self.assertEqual(course['id'], 2)
        self.assertEqual(course['code'], 'CS1500')
        self.assertEqual(course['teacher'], '高女士')
        self.assertEqual(course['semester'], None)
        actions = review['actions']
        self.assertEqual(actions['approves'], 1)
        self.assertEqual(actions['disapproves'], 0)
        self.assertEqual(actions['action'], 1)
        self.assertEqual(review['is_mine'], True)
        self.assertEqual(review['rating'], 3)
        self.assertEqual(review['comment'], 'TEST')
        self.assertEqual(review['score'], 'W')
        self.assertEqual(review['moderator_remark'], None)

    def test_course_avg_count(self):
        course = Course.objects.get(code='CS1500')
        response = self.client.get(f'/api/course/{course.id}/').json()
        self.assertEqual(response['rating']['count'], 1)
        self.assertEqual(response['rating']['avg'], 3)

    def test_get_course_review(self):
        course = Course.objects.get(code='CS1500')
        response = self.client.get(f'/api/course/{course.id}/review/').json()
        self.assertEqual(len(response), 1)
        self.assertNotIn('course', response[0].keys())

    def write_review(self, course: Course, semester: Semester):
        data = {'course': course.id, 'semester': semester.id, 'score': '100', 'comment': 'TEST', 'rating': 5}
        response = self.client.post(self.endpoint, data)
        return response

    def test_write(self):
        course = Course.objects.get(code='CS2500')
        semester = Semester.objects.get(name='2021-2022-2')
        response = self.write_review(course, semester)
        self.assertEqual(response.status_code, 201)
        response = self.client.get(self.endpoint).json()
        self.assertEqual(response['count'], 2)
        response = self.client.get(f'/api/course/{course.id}/').json()
        self.assertEqual(response['rating']['count'], 1)
        self.assertEqual(response['rating']['avg'], 5)

    def test_unique(self):
        course = Course.objects.get(code='CS1500')
        semester = Semester.objects.get(name='2021-2022-2')
        response = self.write_review(course, semester)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], '已经点评过这门课，如需修改请联系管理员')

    def test_mine(self):
        response = self.client.get(self.endpoint + 'mine/').json()
        self.assertEqual(len(response), 1)

    def test_missing_argument(self):
        course = Course.objects.get(code='CS2500')
        semester = Semester.objects.get(name='2021-2022-2')
        response = self.client.post(self.endpoint,
                                    {'course': course.id, 'semester': semester.id, 'comment': 'TEST', 'score': '100'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('rating', response.json())
        response = self.client.post(self.endpoint,
                                    {'semester': semester.id, 'score': '100', 'comment': 'TEST', 'rating': 5})
        self.assertEqual(response.status_code, 400)
        self.assertIn('course', response.json())
        response = self.client.post(self.endpoint,
                                    {'course': course.id, 'semester': semester.id, 'score': '100', 'rating': 5})
        self.assertEqual(response.status_code, 400)
        self.assertIn('comment', response.json())
        response = self.client.post(self.endpoint,
                                    {'course': course.id, 'score': '100', 'comment': 'TEST', 'rating': 5})
        self.assertEqual(response.status_code, 201)  # 允许学期为空


class ActionTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.review = create_review()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = f'/api/review/{self.review.id}/reaction/'

    def test_only_post(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 405)

    def test_empty_data(self):
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, 400)

    def test_approve(self):
        response = self.client.post(self.endpoint, {'action': 1}).json()
        self.assertEqual(response['action'], '1')
        self.assertEqual(response['approves'], 1)
        self.assertEqual(response['disapproves'], 0)

    def test_disapprove(self):
        response = self.client.post(self.endpoint, {'action': -1}).json()
        self.assertEqual(response['action'], '-1')
        self.assertEqual(response['approves'], 0)
        self.assertEqual(response['disapproves'], 1)

    def test_unset(self):
        response = self.client.post(self.endpoint, {'action': 0}).json()
        self.assertEqual(response['action'], '0')
        self.assertEqual(response['approves'], 0)
        self.assertEqual(response['disapproves'], 0)
