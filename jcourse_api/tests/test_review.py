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
        reactions = review['reactions']
        self.assertEqual(reactions['approves'], 1)
        self.assertEqual(reactions['disapproves'], 0)
        self.assertEqual(reactions['reaction'], 1)
        self.assertEqual(review['is_mine'], True)
        self.assertEqual(review['rating'], 3)
        self.assertEqual(review['comment'], 'TEST')
        self.assertEqual(review['score'], 'W')
        self.assertEqual(review['moderator_remark'], None)
        self.assertIsNotNone(review['created_at'])
        self.assertIsNotNone(review['modified_at'])
        self.assertEqual(review['modified_at'], review['created_at'])

    def test_order_by(self):
        review = create_review('test2')
        ReviewReaction.objects.create(review=review, user=self.user, reaction=1)
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
        self.assertEqual(course['name'], '计算机科学导论')
        self.assertEqual(course['id'], self.review.course_id)
        reactions = review['reactions']
        self.assertEqual(reactions['approves'], 1)
        self.assertEqual(reactions['disapproves'], 0)
        self.assertEqual(reactions['reaction'], 1)
        self.assertEqual(review['is_mine'], True)
        self.assertEqual(review['rating'], 3)
        self.assertEqual(review['comment'], 'TEST')
        self.assertEqual(review['score'], 'W')
        self.assertEqual(review['moderator_remark'], None)
        self.assertIsNotNone(review['created_at'])
        self.assertIsNotNone(review['modified_at'])
        self.assertEqual(review['modified_at'], review['created_at'])

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
        reactions = review['reactions']
        self.assertEqual(reactions['approves'], 1)
        self.assertEqual(reactions['disapproves'], 0)
        self.assertEqual(reactions['reaction'], 1)
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
        self.assertIsNotNone(review['modified_at'])

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
        self.assertEqual(response.json()['error'], '已经点评过这门课，如需修改，请从“修改点评”入口进入')

    def test_mine(self):
        response = self.client.get(self.endpoint + 'mine/').json()
        self.assertEqual(len(response), 1)

    def test_location(self):
        response = self.client.get(f"{self.endpoint}{self.review.id}/location/").json()
        self.assertEqual(response, {"course": self.review.course_id, "location": 0})

        review2 = create_review("test2")
        response = self.client.get(f"{self.endpoint}{review2.id}/location/").json()
        self.assertEqual(response, {"course": review2.course_id, "location": 0})

        response = self.client.get(f"{self.endpoint}{self.review.id}/location/").json()
        self.assertEqual(response, {"course": self.review.course_id, "location": 1})

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


class SpamTest(TestCase):

    def setUp(self) -> None:
        create_test_env()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/review/'

    def test_spam(self):
        courses = Course.objects.all()
        course = courses[0]
        response = self.client.post(self.endpoint,
                                    {'course': course.id, 'score': '100', 'comment': 'TEST', 'rating': 5})
        self.assertEqual(response.status_code, 201)
        course = courses[1]
        response = self.client.post(self.endpoint,
                                    {'course': course.id, 'score': '100', 'comment': 'TEST', 'rating': 5})
        self.assertEqual(response.status_code, 201)
        course = courses[2]
        response = self.client.post(self.endpoint,
                                    {'course': course.id, 'score': '100', 'comment': 'TEST', 'rating': 5})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "由于大量刷点评，您已被封号，如有疑问请邮件联系")


class ReviewRevisionTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.review = create_review()
        self.client = APIClient()
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        self.endpoint = '/api/review'
        self.semester = Semester.objects.get(name='2021-2022-1')

    def test_create_revision_on_review(self):
        data = {'course': self.review.course_id, 'semester': self.review.semester_id, 'score': '100',
                'comment': 'TEST2', 'rating': 3}
        response = self.client.put(f'{self.endpoint}/{self.review.id}/', data)
        review = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(review['modified_at'])
        revision = ReviewRevision.objects.filter(review_id=self.review.id)
        self.assertIsNotNone(revision)
        revision = revision.first()
        self.assertEqual(revision.comment, self.review.comment)
        self.assertEqual(revision.score, self.review.score)
        self.assertEqual(revision.rating, self.review.rating)
        self.assertEqual(revision.course_id, self.review.course_id)
        self.assertEqual(revision.semester_id, self.review.semester_id)
        self.assertEqual(revision.user_id, self.user.id)

    def test_only_admin(self):
        response = self.client.get(f'{self.endpoint}/{self.review.id}/revision/')
        self.assertEqual(response.status_code, 403)

    def test_get_revision(self):
        data = {'course': self.review.course_id, 'semester': self.review.semester_id, 'score': '100',
                'comment': 'TEST2', 'rating': 3}
        response = self.client.put(f'{self.endpoint}/{self.review.id}/', data)
        self.assertEqual(response.status_code, 200)
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(f'{self.endpoint}/{self.review.id}/revision/')
        revisions = response.json()
        self.assertEqual(revisions["count"], 1)
        revision = revisions["results"][0]
        self.assertEqual(revision["comment"], self.review.comment)
        self.assertEqual(revision["score"], self.review.score)
        self.assertEqual(revision["rating"], self.review.rating)
        self.assertEqual(revision["course"]['id'], self.review.course.id)
        self.assertEqual(revision["course"]['code'], self.review.course.code)
        self.assertEqual(revision["course"]['name'], self.review.course.name)
        self.assertEqual(revision["course"]['teacher'], self.review.course.main_teacher.name)
        self.assertEqual(revision["semester"], self.review.semester.name)


class ReviewReactionTest(TestCase):
    def setUp(self) -> None:
        create_test_env()
        self.review = create_review()
        self.client = APIClient()
        self.user = User.objects.create(username='test2')
        self.client.force_login(self.user)
        self.endpoint = f'/api/review/{self.review.id}/reaction/'

    def check_review_action(self, reaction: int, approves: int, disapproves: int):
        response = self.client.get(f'/api/review/{self.review.id}/').json()
        self.assertEqual(response['reactions']['reaction'], reaction)
        self.assertEqual(response['reactions']['approves'], approves)
        self.assertEqual(response['reactions']['disapproves'], disapproves)

    def test_wrong_pk(self):
        response = self.client.post('/api/review//reaction/', {'reaction': 1})
        self.assertEqual(response.status_code, 404)
        response = self.client.post('/api/review/0/reaction/', {'reaction': 1})
        self.assertEqual(response.status_code, 404)

    def test_only_post(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 405)

    def test_empty_data(self):
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, 400)

    def test_approve(self):
        response = self.client.post(self.endpoint, {'reaction': 1})
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(response['reaction'], '1')
        self.assertEqual(response['approves'], 2)
        self.assertEqual(response['disapproves'], 0)
        self.check_review_action(1, 2, 0)

    def test_disapprove(self):
        response = self.client.post(self.endpoint, {'reaction': -1})
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(response['reaction'], '-1')
        self.assertEqual(response['approves'], 1)
        self.assertEqual(response['disapproves'], 1)
        self.check_review_action(-1, 1, 1)

    def test_unset(self):
        self.user = User.objects.get(username='test')
        self.client.force_login(self.user)
        response = self.client.post(self.endpoint, {'reaction': 0}).json()
        self.assertEqual(response['reaction'], '0')
        self.assertEqual(response['approves'], 0)
        self.assertEqual(response['disapproves'], 0)
        self.check_review_action(0, 0, 0)


class FilterTest(TestCase):
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

        self.review1 = Review.objects.create(user=self.user, course=self.course1, comment='TEST', rating=5, score='W',
                                             semester=Semester.objects.get(name='2021-2022-1'),
                                             modified_at=timezone.now() - timezone.timedelta(days=1),
                                             approve_count=2)
        self.review2 = Review.objects.create(user=self.user, course=self.course2, comment='TEST', rating=3, score='W',
                                             semester=Semester.objects.get(name='2021-2022-2'))
        self.review3 = Review.objects.create(user=self.user, course=self.course4, comment='TEST', rating=3, score='W',
                                             semester=Semester.objects.get(name='2021-2022-2'))
        self.review4 = Review.objects.create(user=self.user, course=self.course5, comment='TEST', rating=3, score='W',
                                             semester=Semester.objects.get(name='2021-2022-2'))

        self.review5 = Review.objects.create(user=self.user2, course=self.course1, comment='TEST', rating=3, score='W',
                                             semester=Semester.objects.get(name='2021-2022-2'),
                                             modified_at=timezone.now() - timezone.timedelta(days=2),
                                             approve_count=3)
        self.review6 = Review.objects.create(user=self.user2, course=self.course4, comment='TEST', rating=3, score='W',
                                             semester=Semester.objects.get(name='2021-2022-1'))
        self.review7 = Review.objects.create(user=self.user3, course=self.course1, comment='TEST', rating=1, score='W',
                                             semester=Semester.objects.get(name='2021-2022-1'),
                                             modified_at=timezone.now() - timezone.timedelta(days=3),
                                             approve_count=1)

        self.semester1 = Semester.objects.get(name='2021-2022-1')
        self.semester2 = Semester.objects.get(name='2021-2022-2')

    def test_body(self):
        response = self.client1.get('/api/review-filter/', {'course_id': str(self.course1.id)}).json()
        self.assertEqual(response['semesters'],
                         [{'id': self.semester2.id, 'name': self.semester2.name, 'count': 1, 'avg': 3.0},
                          {'id': self.semester1.id, 'name': self.semester1.name, 'count': 2, 'avg': 3.0}])
        self.assertEqual(response['ratings'],
                         [{'rating': 5, 'count': 1}, {'rating': 3, 'count': 1}, {'rating': 1, 'count': 1}])

    def test_order(self):
        course_id = self.course1.id
        response = self.client1.get(f'/api/course/{course_id}/review/').json()
        self.assertEqual(len(response['results']), 3)
        response = self.client1.get(f'/api/course/{course_id}/review/', {'order': 0}).json()
        self.assertEqual(response['results'][0]['id'], self.review1.id)
        response = self.client1.get(f'/api/course/{course_id}/review/', {'order': 1}).json()
        self.assertEqual(response['results'][0]['id'], self.review7.id)
        response = self.client1.get(f'/api/course/{course_id}/review/', {'order': 2}).json()
        self.assertEqual(response['results'][0]['id'], self.review5.id)
        response = self.client2.get(f'/api/course/{course_id}/review/', {'order': 3}).json()
        self.assertEqual(response['results'][0]['id'], self.review1.id)
        response = self.client2.get(f'/api/course/{course_id}/review/', {'order': 4}).json()
        self.assertEqual(response['results'][0]['id'], self.review7.id)
        response = self.client2.get(f'/api/course/{course_id}/review/', {'order': 5}).json()
        self.assertEqual(len(response['results']), 0)

    def test_semester_filter(self):
        course_id = self.course1.id
        response = self.client1.get(f'/api/course/{course_id}/review/', {'semester': self.semester1.id}).json()
        self.assertEqual(len(response['results']), 2)

    def test_rating_filter(self):
        course_id = self.course1.id
        response = self.client1.get(f'/api/course/{course_id}/review/', {'rating': 1}).json()
        self.assertEqual(len(response['results']), 1)
        self.assertEqual(response['results'][0]['id'], self.review7.id)
