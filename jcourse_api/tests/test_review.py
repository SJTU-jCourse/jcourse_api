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
        self.semester = Semester.objects.get(name='2021-2022-1')

    def test_list(self):
        response = self.client.get(self.endpoint).json()
        self.assertEqual(response['count'], 1)
        review = response['results'][0]
        self.assertEqual(review['id'], self.review.id)
        self.assertEqual(review['semester'], self.semester.name)
        course = review['course']
        self.assertEqual(course['code'], 'CS1500')
        self.assertEqual(course['teacher'], '高女士')
        # self.assertEqual(course['semester'], None)
        actions = review['actions']
        self.assertEqual(actions['approves'], 1)
        self.assertEqual(actions['disapproves'], 0)
        self.assertEqual(actions['action'], 1)
        self.assertEqual(review['is_mine'], True)
        self.assertEqual(review['rating'], 3)
        self.assertEqual(review['comment'], 'TEST')
        self.assertEqual(review['score'], 'W')
        self.assertEqual(review['moderator_remark'], None)
        self.assertIsNotNone(review['created'])
        self.assertIsNone(review['modified'])

    def test_order_by(self):
        review = create_review('test2')
        Action.objects.create(review=review, user=self.user, action=1)
        response = self.client.get(self.endpoint, {'order': 'approves'}).json()
        self.assertEqual(response['count'], 2)
        self.assertEqual(response['results'][0]['id'], review.id)
        self.assertEqual(response['results'][1]['id'], self.review.id)

    def test_retrieve(self):
        response = self.client.get(self.endpoint + f'{self.review.id}/')
        review = response.json()
        self.assertEqual(review['id'], self.review.id)
        self.assertEqual(review['semester']['name'], self.semester.name)
        self.assertEqual(review['semester']['id'], self.semester.id)
        course = review['course']
        self.assertEqual(course['code'], 'CS1500')
        self.assertEqual(course['teacher'], '高女士')
        self.assertEqual(course['semester'], None)
        self.assertEqual(course['name'], '计算机科学导论')
        self.assertEqual(course['id'], self.review.course_id)
        actions = review['actions']
        self.assertEqual(actions['approves'], 1)
        self.assertEqual(actions['disapproves'], 0)
        self.assertEqual(actions['action'], 1)
        self.assertEqual(review['is_mine'], True)
        self.assertEqual(review['rating'], 3)
        self.assertEqual(review['comment'], 'TEST')
        self.assertEqual(review['score'], 'W')
        self.assertEqual(review['moderator_remark'], None)
        self.assertIsNotNone(review['created'])
        self.assertIsNone(review['modified'])

    def test_course_avg_count(self):
        course = Course.objects.get(code='CS1500')
        response = self.client.get(f'/api/course/{course.id}/').json()
        self.assertEqual(response['rating']['count'], 1)
        self.assertEqual(response['rating']['avg'], 3)

    def test_get_course_review(self):
        course = Course.objects.get(code='CS1500')
        response = self.client.get(f'/api/course/{course.id}/review/').json()
        response = response['results']
        self.assertEqual(len(response), 1)
        self.assertNotIn('course', response[0].keys())
        review = response[0]
        self.assertEqual(review['semester'], self.semester.name)
        actions = review['actions']
        self.assertEqual(actions['approves'], 1)
        self.assertEqual(actions['disapproves'], 0)
        self.assertEqual(actions['action'], 1)
        self.assertEqual(review['is_mine'], True)
        self.assertEqual(review['rating'], 3)
        self.assertEqual(review['comment'], 'TEST')
        self.assertEqual(review['score'], 'W')
        self.assertEqual(review['moderator_remark'], None)

    def write_review(self, course: Course, semester: Semester):
        data = {'course': course.id, 'semester': semester.id, 'score': '100', 'comment': 'TEST', 'rating': 5}
        response = self.client.post(self.endpoint, data)
        return response

    def test_put_my_review(self):
        data = {'course': self.review.course_id, 'semester': self.review.semester_id, 'score': '100',
                'comment': 'TEST2', 'rating': 3}
        response = self.client.put(self.endpoint + f'{self.review.id}/', data)
        review = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(review['modified'])

    def test_put_others_review(self):
        review = create_review('test2', 'CS1500', 5)
        data = {'course': self.review.course_id, 'semester': self.review.semester_id, 'score': '100',
                'comment': 'TEST2', 'rating': 3}
        response = self.client.put(self.endpoint + f'{review.id}/', data)
        self.assertEqual(response.status_code, 403)

    def test_modify_rating(self):
        data = {'course': self.review.course_id, 'semester': self.review.semester_id, 'score': '100',
                'comment': 'TEST2', 'rating': 5}
        self.client.put(self.endpoint + f'{self.review.id}/', data)
        response = self.client.get(f'/api/course/{self.review.course_id}/').json()
        self.assertEqual(response['rating']['count'], 1)
        self.assertEqual(response['rating']['avg'], 5)

    def test_delete_my_review(self):
        response = self.client.delete(self.endpoint + f'{self.review.id}/')
        self.assertEqual(response.status_code, 204)

    def test_delete_others_review(self):
        review = create_review('test2', 'CS1500', 5)
        response = self.client.delete(self.endpoint + f'{review.id}/')
        self.assertEqual(response.status_code, 403)

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

    def check_review_action(self, action: int, approves: int, disapproves: int):
        response = self.client.get(f'/api/review/{self.review.id}/').json()
        self.assertEqual(response['actions']['action'], action)
        self.assertEqual(response['actions']['approves'], approves)
        self.assertEqual(response['actions']['disapproves'], disapproves)

    def test_wrong_pk(self):
        response = self.client.post('/api/review//reaction/', {'action': 1})
        self.assertEqual(response.status_code, 404)
        response = self.client.post('/api/review/0/reaction/', {'action': 1})
        self.assertEqual(response.status_code, 404)

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
        self.check_review_action(1, 1, 0)

    def test_disapprove(self):
        response = self.client.post(self.endpoint, {'action': -1}).json()
        self.assertEqual(response['action'], '-1')
        self.assertEqual(response['approves'], 0)
        self.assertEqual(response['disapproves'], 1)
        self.check_review_action(-1, 0, 1)

    def test_unset(self):
        response = self.client.post(self.endpoint, {'action': 0}).json()
        self.assertEqual(response['action'], '0')
        self.assertEqual(response['approves'], 0)
        self.assertEqual(response['disapproves'], 0)
        self.check_review_action(0, 0, 0)
