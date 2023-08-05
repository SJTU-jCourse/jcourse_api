from django.test import TestCase
from rest_framework.test import APIClient

from jcourse_api.tests import *


class SemesterTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/semester/'

    def test_auth(self):
        client = APIClient()  # another client
        response = client.get(self.endpoint)
        self.assertEqual(response.status_code, 403)

    def test_body(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        semesters = Semester.objects.all()
        expected = [{'id': semester.pk, 'name': semester.name, 'available': semester.available}
                    for semester in semesters]
        self.assertEqual(response.json(), expected)

    def test_readonly(self):
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, 405)
        response = self.client.put(self.endpoint)
        self.assertEqual(response.status_code, 405)
        response = self.client.delete(self.endpoint)
        self.assertEqual(response.status_code, 405)

    def test_auto_slash(self):
        response = self.client.post('/api/semester')
        self.assertEqual(response.status_code, 301)


class CourseTest(TestCase):

    def setUp(self) -> None:
        create_test_env()
        self.review = create_review()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/course/'

    def test_auth(self):
        client = APIClient()  # another client
        response = client.get(self.endpoint)
        self.assertEqual(response.status_code, 403)

    def test_pagination(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(response['count'], 4)
        self.assertIsNone(response['next'])
        self.assertIsNone(response['previous'])

    def test_list(self):
        response = self.client.get(self.endpoint)
        courses = response.json()['results']
        self.assertEqual(courses[0]['name'], '计算机科学导论')
        self.assertEqual(courses[0]['categories'], [])
        self.assertEqual(courses[0]['department'], 'SEIEE')
        self.assertEqual(courses[0]['teacher'], '高女士')
        self.assertEqual(courses[0]['rating'], {'count': 1, 'avg': 3.0})
        self.assertEqual(courses[0]['code'], 'CS1500')
        self.assertEqual(courses[0]['credit'], 4.0)

    def test_only_has_review(self):
        response = self.client.get(self.endpoint, {'onlyhasreviews': ''})
        courses = response.json()['results']
        for course in courses:
            self.assertGreater(course['rating']['count'], 0)

    def test_sort_by_avg(self):
        create_review('test', 'CS2500', 5)
        create_review('test2', 'CS1500', 3)
        response = self.client.get(self.endpoint, {'onlyhasreviews': 'avg'})
        courses = response.json()['results']
        self.assertEqual(courses[0]['code'], 'CS2500')
        self.assertEqual(courses[1]['code'], 'CS1500')

    def test_sort_by_count(self):
        create_review('test', 'CS2500', 5)
        create_review('test2', 'CS1500', 3)
        response = self.client.get(self.endpoint, {'onlyhasreviews': 'count'})
        courses = response.json()['results']
        self.assertEqual(courses[0]['code'], 'CS1500')
        self.assertEqual(courses[1]['code'], 'CS2500')

    def test_filter(self):
        response = self.client.get(self.endpoint, {'categories': Category.objects.get(name='通识').pk})
        courses = response.json()['results']
        for course in courses:
            self.assertEqual(course['categories'], ['通识'])

        response = self.client.get(self.endpoint, {'department': Department.objects.get(name='SEIEE').pk})
        courses = response.json()['results']
        for course in courses:
            self.assertEqual(course['department'], 'SEIEE')

    def test_retrieve(self):
        test_course = Course.objects.get(name='思想道德修养与法律基础', main_teacher=Teacher.objects.get(name='梁女士'))
        response = self.client.get(self.endpoint + f"{test_course.pk}/")
        course = response.json()
        self.assertEqual(course['name'], '思想道德修养与法律基础')
        self.assertEqual(course['categories'], ['通识'])
        self.assertEqual(course['department'], 'PHYSICS')
        main_teacher = course['main_teacher']
        teacher_group = course['teacher_group']
        self.assertEqual(main_teacher['name'], '梁女士')
        self.assertEqual(main_teacher['tid'], '2')
        self.assertEqual(len(teacher_group), 1)
        self.assertEqual(course['rating'], {'count': 0, 'avg': 0.0})
        self.assertEqual(course['code'], 'MARX1001')
        self.assertEqual(course['credit'], 3.0)
        related_teachers = course['related_teachers']
        self.assertEqual(len(related_teachers), 1)
        self.assertEqual(related_teachers[0]['tname'], '赵先生')
        # self.assertEqual(related_teachers[0]['id'], 4)
        self.assertEqual(related_teachers[0]['avg'], 0)
        self.assertEqual(related_teachers[0]['count'], 0)
        self.assertEqual(len(course['related_courses']), 0)
        self.assertIsNone(course['moderator_remark'])

    def test_not_found(self):
        response = self.client.get(self.endpoint + '5/')
        self.assertEqual(response.status_code, 404)


class FilterTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/course-filter/'

    def test_body(self):
        response = self.client.get(self.endpoint).json()
        self.assertEqual(response['categories'],
                         [{'id': Category.objects.get(name='通识').pk, 'count': 2, 'name': '通识'}])
        self.assertEqual(response['departments'],
                         [{'id': Department.objects.get(name='PHYSICS').pk, 'count': 2, 'name': 'PHYSICS'},
                          {'id': Department.objects.get(name='SEIEE').pk, 'count': 2, 'name': 'SEIEE'}])

    def test_delete_course(self):
        Course.objects.all().delete()
        response = self.client.get(self.endpoint).json()
        self.assertEqual(response['categories'], [])
        self.assertEqual(response['departments'], [])


class SearchTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.review = create_review()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/search/'

    def test_none(self):
        response = self.client.get(self.endpoint).json()
        self.assertEqual(response['count'], 0)

    def test_code(self):
        response = self.client.get(self.endpoint, {'q': 'CS'}).json()
        codes = [course['code'] for course in response['results']]
        self.assertIn('CS1500', codes)
        self.assertIn('CS2500', codes)

    def test_course_name(self):
        response = self.client.get(self.endpoint, {'q': '计算机'}).json()
        names = [course['name'] for course in response['results']]
        self.assertIn('计算机科学导论', names)

    def test_teacher_name(self):
        response = self.client.get(self.endpoint, {'q': '高女士'}).json()
        names = [course['name'] for course in response['results']]
        self.assertIn('计算机科学导论', names)

    def test_pinyin(self):
        response = self.client.get(self.endpoint, {'q': 'gxf'}).json()
        names = [course['name'] for course in response['results']]
        self.assertIn('计算机科学导论', names)
        response = self.client.get(self.endpoint, {'q': 'liangqin'}).json()
        names = [course['name'] for course in response['results']]
        self.assertIn('思想道德修养与法律基础', names)


class CourseInReviewTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/course-in-review/'
        self.course = Course.objects.filter(code='CS1500').first()

    def test_search(self):
        response = self.client.get(self.endpoint, {'q': 'CS1500'}).json()
        response = response['results']
        self.assertEqual(response[0]['id'], self.course.pk)
        self.assertEqual(response[0]['code'], 'CS1500')
        self.assertEqual(response[0]['name'], '计算机科学导论')
        self.assertEqual(response[0]['teacher'], '高女士')

    def test_retrieve(self):
        response = self.client.get(self.endpoint + f'{self.course.pk}/').json()
        self.assertEqual(response['id'], self.course.pk)
        self.assertEqual(response['code'], 'CS1500')
        self.assertEqual(response['name'], '计算机科学导论')
        self.assertEqual(response['teacher'], '高女士')
