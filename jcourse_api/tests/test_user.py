from unittest.mock import patch

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

    def test_points(self):
        result = get_user_point(self.user)
        self.assertEqual(result['points'], 6)
        result = get_user_point(User.objects.create(username='test2'))
        self.assertEqual(result['points'], 0)


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
             'code': '(2019-2020-1)-CS1500-1', 'course': {'code': 'CS1500', 'name': '计算机科学导论', 'kind': 'sjtu.course'},
             'teachers': [{'name': '高女士', 'kind': 'canvas.profile'}],
             'organize': {'id': '03000', 'name': '电子信息与电气工程学院'}, 'hours': 32, 'credits': 3},
            {'name': '(2019-2020-1)-TH000-1', 'kind': 'sjtu.lesson', 'bsid': '',
             'code': '(2019-2020-1)-TH000-1', 'course': {'code': 'TH000', 'name': '思想道德修养与法律基础', 'kind': 'sjtu.course'},
             'teachers': [{'name': '梁女士', 'kind': 'canvas.profile'}],
             'organize': {'id': '03000', 'name': '马克思主义学院'}, 'hours': 32, 'credits': 2}]}

    def test_no_token(self):
        response = self.client.post(self.endpoint + '2021-2022-1/')
        self.assertEqual(response.status_code, 401)

    def test_parse(self):
        codes, teachers = parse_jaccount_courses(SyncTest.jaccount_api())
        self.assertEqual(codes, ['CS1500', 'TH000'])
        self.assertEqual(teachers, ['高女士', '梁女士'])

    def test_find_exist(self):
        ids = find_exist_course_ids(['TH000'], ['梁女士'])
        target = Course.objects.get(code='MARX1001', main_teacher__name='梁女士')
        self.assertEqual(target.id, ids[0]['id'])

    def test_sync(self):
        courses = Course.objects.filter(code='MARX1001', main_teacher__name='梁女士').values('id')
        sync_enroll_course(self.user, courses, '2021-2022-1')
        sync_enroll_course(self.user, courses, '2021-2022-1')  # test duplicated enroll
        enrolled = EnrollCourse.objects.filter(user=self.user)
        self.assertEqual(len(enrolled), 1)
        self.assertEqual(enrolled[0].course_id, courses[0]['id'])
        self.assertEqual(enrolled[0].semester.name, '2021-2022-1')
        courses = Course.objects.filter(code='CS1500', main_teacher__name='高女士').values('id')
        sync_enroll_course(self.user, courses, None)
        enrolled = EnrollCourse.objects.get(user=self.user, course__code='CS1500')
        self.assertEqual(enrolled.semester, None)

    @patch('jcourse_api.views.get_jaccount_lessons')
    def test_e2e(self, mock_jac):
        mock_jac.return_value = SyncTest.jaccount_api()
        session = self.client.session
        session['token'] = {'expires_in': 0, 'token_type': 'Bearer',
                            'refresh_token': '',
                            'id_token': '',
                            'access_token': '', 'expires_at': 0}
        session.save()
        response = self.client.post(self.endpoint + '2021-2022-1/')
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(len(response), 2)
        enrolled = EnrollCourse.objects.filter(user=self.user)
        self.assertEqual(len(enrolled), 2)
