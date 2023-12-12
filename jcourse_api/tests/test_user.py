import json
from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from rest_framework.test import APIClient

from jcourse_api.tests import *
from jcourse_api.views import *


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


class UserPointTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.review = create_review()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        UserPoint.objects.create(user=self.user, value=100, description='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/points/'

    def test_empty_points(self):
        user = User.objects.create(username='test2')
        self.client.force_login(user)
        response = self.client.get(self.endpoint).json()
        self.assertEqual(response['points'], 0)
        self.assertEqual(response['details'], [])

    def test_points(self):
        response = self.client.get(self.endpoint).json()
        self.assertEqual(response['points'], 100)
        details = response['details']
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]['value'], 100)

    def test_bad_reviews(self):
        user2 = User.objects.create(username='test2')
        user3 = User.objects.create(username='test3')
        user4 = User.objects.create(username='test4')
        ReviewReaction.objects.create(user=user2, review=self.review, reaction=-1)
        ReviewReaction.objects.create(user=user3, review=self.review, reaction=-1)
        ReviewReaction.objects.create(user=user4, review=self.review, reaction=-1)
        response = self.client.get(self.endpoint).json()
        self.assertEqual(response['points'], 100)


class EnrollLessonTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.review = create_review()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/lesson/'
        courses = Course.objects.all()
        self.semester = Semester.objects.first()
        for course in courses:
            EnrollCourse.objects.create(user=self.user, course=course, semester=self.semester)

    def test_list(self):
        response = self.client.get(self.endpoint).json()
        self.assertEqual(len(response), 4)


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
        self.assertEqual(response['comment'], 'TEST')
        self.assertIn('created_at', response)
        self.assertIn('reply', response)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '选课社区反馈')
        self.assertEqual(response['user'], self.user.id)

    def test_list(self):
        self.client.post(self.endpoint, {'comment': 'TEST'})
        response = self.client.get(self.endpoint).json()
        self.assertEqual(len(response), 1)


class SyncTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/sync-lessons/'

    @classmethod
    def jaccount_api(cls):
        return {'errno': 0, 'error': 'success', 'total': 0, 'entities': [
            {'name': '(2019-2020-1)-CS1500-1', 'kind': 'sjtu.lesson', 'bsid': '',
             'code': '(2019-2020-1)-CS1500-1',
             'course': {'code': 'CS1500', 'name': '计算机科学导论', 'kind': 'sjtu.course'},
             'teachers': [{'name': '高女士', 'kind': 'canvas.profile'}],
             'organize': {'id': '03000', 'name': '电子信息与电气工程学院'}, 'hours': 32, 'credits': 3},
            {'name': '(2019-2020-1)-TH000-1', 'kind': 'sjtu.lesson', 'bsid': '',
             'code': '(2019-2020-1)-TH000-1',
             'course': {'code': 'MARX1001', 'name': '思想道德修养与法律基础', 'kind': 'sjtu.course'},
             'teachers': [{'name': '梁女士', 'kind': 'canvas.profile'}],
             'organize': {'id': '03000', 'name': '马克思主义学院'}, 'hours': 32, 'credits': 2}]}

    def test_no_token(self):
        response = self.client.post(self.endpoint + '2021-2022-1/')
        self.assertEqual(response.status_code, 401)

    def test_parse(self):
        codes, teachers = parse_jaccount_courses(SyncTest.jaccount_api())
        self.assertEqual(codes, ['CS1500', 'MARX1001'])
        self.assertEqual(teachers, ['高女士', '梁女士'])

    def test_find_exist(self):
        ids = find_exist_course_ids(['MARX1001'], ['梁女士'])
        target = Course.objects.get(code='MARX1001', main_teacher__name='梁女士')
        self.assertEqual(target.id, ids[0])

    def create_former_enroll(self):
        withdrawn_course = Course.objects.get(code='MARX1001', main_teacher__name='赵先生')
        semester = Semester.objects.get(name='2021-2022-1')
        EnrollCourse.objects.create(user=self.user, course=withdrawn_course, semester=semester)

    def test_sync_add(self):
        course_ids = Course.objects.filter(code='MARX1001', main_teacher__name='梁女士').values_list('id', flat=True)
        sync_enroll_course(self.user, course_ids, '2021-2022-1')
        sync_enroll_course(self.user, course_ids, '2021-2022-1')  # test duplicated enroll
        enrolled = EnrollCourse.objects.filter(user=self.user)
        self.assertEqual(len(enrolled), 1)
        self.assertEqual(enrolled[0].course_id, course_ids[0])
        self.assertEqual(enrolled[0].semester.name, '2021-2022-1')
        course_ids = Course.objects.filter(code='CS1500', main_teacher__name='高女士').values_list('id', flat=True)
        sync_enroll_course(self.user, course_ids, None)
        enrolled = EnrollCourse.objects.get(user=self.user, course__code='CS1500')
        self.assertEqual(enrolled.semester, None)

    def test_sync_delete(self):
        self.create_former_enroll()
        course_ids = Course.objects.filter(code='CS1500', main_teacher__name='高女士').values_list('id', flat=True)
        sync_enroll_course(self.user, course_ids, '2021-2022-1')
        enrolled = EnrollCourse.objects.filter(user=self.user)
        self.assertEqual(len(enrolled), 1)
        self.assertEqual(enrolled[0].course_id, course_ids[0])
        self.assertEqual(enrolled[0].semester.name, '2021-2022-1')

    @patch('jcourse_api.views.enroll.get_jaccount_lessons')
    def test_e2e(self, mock_jac):
        mock_jac.return_value = SyncTest.jaccount_api()
        session = self.client.session
        session['token'] = {'expires_in': 0, 'token_type': 'Bearer',
                            'refresh_token': '',
                            'id_token': '',
                            'access_token': '', 'expires_at': 0}
        session.save()
        self.create_former_enroll()
        response = self.client.post(self.endpoint + '2021-2022-1/')
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(len(response), 2)
        enrolled = EnrollCourse.objects.filter(user=self.user)
        self.assertEqual(len(enrolled), 2)


class SyncV2Test(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/sync-lessons-v2/'

    def test_e2e(self):
        response = self.client.post(self.endpoint, data=json.dumps([
            {'code': 'CS1500', 'name': '计算机科学导论', 'teachers': '高女士', 'semester': '2021-2022-1'},
            {'code': 'MARX1001', 'name': '思想道德修养与法律基础', 'teachers': '梁女士', 'semester': '2021-2022-1'}
        ]), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        enrolled = EnrollCourse.objects.filter(user=self.user)
        self.assertEqual(len(enrolled), 2)
