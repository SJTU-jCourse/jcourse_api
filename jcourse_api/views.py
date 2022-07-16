import django_filters
from django.core.mail import send_mail
from django.db.models import Sum, OuterRef, Subquery
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.vary import vary_on_cookie
from django_filters import BaseInFilter, NumberFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

import jcourse.settings
from jcourse_api.permissions import IsOwnerOrReadOnly
from jcourse_api.serializers import *
from jcourse_api.throttles import ActionRateThrottle
from oauth.views import hash_username, jaccount


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class CourseFilter(django_filters.FilterSet):
    category = NumberInFilter(field_name="category", lookup_expr="in")
    department = NumberInFilter(field_name="department", lookup_expr="in")

    class Meta:
        model = Course
        fields = ['category', 'department']


def get_course_list_queryset(user: User):
    my_review = Review.objects.filter(user=user, course_id=OuterRef('pk')).values('pk')
    my_enroll_semester = EnrollCourse.objects.filter(user=user, course_id=OuterRef('pk')).values('semester')

    return Course.objects.select_related('main_teacher', 'category', 'department').annotate(
        semester=Subquery(my_enroll_semester[:1]),
        is_reviewed=Subquery(my_review[:1]))


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CourseFilter

    def get_queryset(self):
        courses = get_course_list_queryset(self.request.user)
        if 'onlyhasreviews' in self.request.query_params:
            courses = courses.filter(review_count__gt=0). \
                annotate(count=F('review_count'), avg=F('review_avg'))
            if self.request.query_params['onlyhasreviews'] == 'count':
                return courses.order_by(F('count').desc(nulls_last=True), F('avg').desc(nulls_last=True))
            return courses.order_by(F('avg').desc(nulls_last=True), F('count').desc(nulls_last=True))
        return courses.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        else:
            return CourseSerializer

    @action(detail=True)
    def review(self, request: Request, pk=None):
        reviews = get_reviews(request.user, 'list').select_related('semester').filter(course_id=pk)
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewInCourseSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = ReviewInCourseSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)


def get_search_course_queryset(q: str, user: User):
    courses = get_course_list_queryset(user)
    if q == '':
        return courses.none()
    courses = courses.filter(
        Q(code__icontains=q) | Q(name__icontains=q) | Q(main_teacher__name__icontains=q) |
        Q(main_teacher__pinyin__iexact=q) | Q(main_teacher__abbr_pinyin__icontains=q))
    return courses


class SearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseListSerializer

    def get_queryset(self):
        q = self.request.query_params.get('q', '')
        return get_search_course_queryset(q, self.request.user)


def get_reviews(user: User, action: str):
    my_action = Action.objects.filter(user=user, review_id=OuterRef('pk')).values('action')
    reviews = Review.objects.select_related('course', 'course__main_teacher', 'semester')
    if action == 'retrieve':
        my_enroll_semester = EnrollCourse.objects.filter(user=user, course_id=OuterRef('course_id')).values('semester')
        return reviews.annotate(
            my_action=Subquery(my_action[:1]), my_enroll_semester=Subquery(my_enroll_semester[:1]))
    return reviews.annotate(my_action=Subquery(my_action[:1]))


class ReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        reviews = get_reviews(self.request.user, self.action)
        if 'order' in self.request.query_params:
            if self.request.query_params['order'] == 'approves':
                return reviews.order_by(F('approve_count').desc(nulls_last=True), F('created').desc(nulls_last=True))
        return reviews

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return CreateReviewSerializer
        elif self.action == 'retrieve':
            return ReviewItemSerializer
        else:
            return ReviewListSerializer

    def perform_create(self, serializer):
        created_time = timezone.now()
        serializer.save(user=self.request.user, modified=created_time, created=created_time)

    def perform_update(self, serializer):
        serializer.save(modified=timezone.now())

    @action(detail=True, methods=['POST'], throttle_classes=[UserRateThrottle, ActionRateThrottle])
    def reaction(self, request: Request, pk=None):
        if 'action' not in request.data:
            return Response({'error': '未指定操作类型！'}, status=status.HTTP_400_BAD_REQUEST)
        if pk is None:
            return Response({'error': '未指定点评id！'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            Action.objects.update_or_create(user=request.user, review_id=pk,
                                            defaults={'action': request.data.get('action')})
            review = Review.objects.get(pk=pk)
        except (Action.DoesNotExist, Review.DoesNotExist):
            return Response({'error': '无指定点评！'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'id': pk,
                         'action': request.data.get('action'),
                         'approves': review.approve_count,
                         'disapproves': review.disapprove_count},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def mine(self, request: Request):
        reviews = get_reviews(self.request.user, 'list').filter(user=request.user)
        serializer = self.get_serializer_class()
        data = serializer(reviews, many=True, context={'request': request}).data
        return Response(data)


class SemesterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Semester.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = SemesterSerializer
    pagination_class = None

    @method_decorator(cache_page(60 * 60 * 2))
    def dispatch(self, request: Request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class NoticeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notice.objects.filter(available=True)
    permission_classes = [IsAuthenticated]
    serializer_class = NoticeSerializer
    pagination_class = None


class CourseInReviewViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseInWriteReviewSerializer

    def get_queryset(self):
        if self.action == 'list':
            q = self.request.query_params.get('q', '')
            return get_search_course_queryset(q, self.request.user)
        elif self.action == 'retrieve':
            return get_course_list_queryset(self.request.user)


class ReportViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer
    pagination_class = None

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)

    def perform_create(self, serializer: serializer_class):
        serializer.save(user=self.request.user)
        if not jcourse.settings.DEBUG:
            data = serializer.data
            email_body = f"内容：\n{data['comment']}\n时间：{data['created']}"
            send_mail('选课社区反馈', email_body, from_email=jcourse.settings.DEFAULT_FROM_EMAIL,
                      recipient_list=[jcourse.settings.ADMIN_EMAIL])


class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        """
        获取当前用户信息
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FilterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        categories = Category.objects.filter(count__gt=0)
        category_serializer = CategorySerializer(categories, many=True)
        departments = Department.objects.filter(count__gt=0)
        department_serializer = DepartmentSerializer(departments, many=True)
        return Response({'categories': category_serializer.data, 'departments': department_serializer.data},
                        status=status.HTTP_200_OK)


class StatisticView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60 * 5))
    def get(self, request: Request):
        return Response({'courses': Course.objects.count(),
                         'courses_with_review': Course.objects.filter(review_count__gt=0).count(),
                         'users': User.objects.count(),
                         'reviews': Review.objects.count()},
                        status=status.HTTP_200_OK)


def get_user_point_with_reviews(user: User, reviews):
    courses = reviews.values_list('course', flat=True)
    approves_count = reviews.aggregate(count=Sum('approve_count'))['count']
    if approves_count is None:
        approves_count = 0
    reviews_count = reviews.count()

    first_reviews = Review.objects.filter(course__in=courses).order_by('course_id', 'created').distinct(
        'course_id').values_list('id', flat=True)
    first_reviews = first_reviews.intersection(reviews)
    first_reviews_count = first_reviews.count()
    first_reviews_approves_count = Review.objects.filter(pk__in=first_reviews).aggregate(count=Sum('approve_count'))[
        'count']
    if first_reviews_approves_count is None:
        first_reviews_approves_count = 0
    additional = UserPoint.objects.filter(user=user)
    additional_point = additional.aggregate(sum=Sum('value'))['sum']
    if additional_point is None:
        additional_point = 0
    addition_details = UserPointSerializer(additional, many=True).data
    points = additional_point + approves_count + first_reviews_approves_count + reviews_count + first_reviews_count
    return {'points': points, 'reviews': reviews_count, 'first_reviews': first_reviews_count,
            'approves': approves_count, 'first_reviews_approves': first_reviews_approves_count,
            'addition': additional_point, 'details': addition_details}


def get_user_point(user: User):
    reviews = Review.objects.filter(user=user).exclude(disapprove_count__gt=F('approve_count') * 2)
    return get_user_point_with_reviews(user, reviews)


class UserPointView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        else:
            return [AllowAny()]

    @method_decorator(cache_page(60 * 5))
    @method_decorator(vary_on_cookie)
    def get(self, request: Request):
        return Response(get_user_point(request.user))

    @csrf_exempt
    def post(self, request: Request):
        account = request.data.get('account', '')
        apikey = request.headers.get('Api-Key', '')
        if account == '' or apikey == '':
            return Response({'detail': 'Bad arguments'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            ApiKey.objects.get(key=apikey, is_enabled=True)
        except ApiKey.DoesNotExist:
            return Response({'detail': 'Bad arguments'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=hash_username(account), is_active=True)
        except User.DoesNotExist:
            return Response({'detail': 'Bad arguments'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(get_user_point(user))


def parse_jaccount_courses(response: dict):
    codes = []
    teachers = []
    for entity in response['entities']:
        codes.append(entity['course']['code'])
        teachers.append(entity['teachers'][0]['name'])
    return codes, teachers


def find_exist_course_ids(codes: list, teachers: list):
    former_codes = FormerCode.objects.filter(old_code__in=codes).values('old_code', 'new_code')
    former_codes_dict = {}
    for former_code in former_codes:
        former_codes_dict[former_code['old_code']] = former_code['new_code']
    conditions = Q(pk=None)
    for code, teacher in zip(codes, teachers):
        if former_codes_dict.get(code, None):
            conditions = conditions | (
                    (Q(code=former_codes_dict[code]) | Q(code=code)) & Q(main_teacher__name=teacher))
        else:
            conditions = conditions | (Q(code=code) & Q(main_teacher__name=teacher))
    return Course.objects.filter(conditions).values_list('id', flat=True)


def sync_enroll_course(user: User, course_ids: list, term: str):
    try:
        semester = Semester.objects.get(name=term)
    except Semester.DoesNotExist:
        semester = None
    enroll_courses = []
    for course_id in course_ids:
        enroll_courses.append(EnrollCourse(user=user, course_id=course_id, semester=semester))
    # remove withdrawn courses
    EnrollCourse.objects.filter(user=user, semester=semester).exclude(course_id__in=course_ids).delete()
    EnrollCourse.objects.bulk_create(enroll_courses, ignore_conflicts=True)


def get_jaccount_lessons(token: dict, term: str):
    return jaccount.get(f'v1/me/lessons/{term}/', token=token, params={"classes": False}).json()


@api_view(['POST'])
def sync_lessons(request: Request, term: str = '2018-2019-2'):
    token = request.session.get('token', None)
    if token is None:
        return Response({'detail': '未授权获取课表信息'}, status=status.HTTP_401_UNAUTHORIZED)
    resp = get_jaccount_lessons(token, term)
    if resp['errno'] == 0:
        codes, teachers = parse_jaccount_courses(resp)
        existed_courses_ids = find_exist_course_ids(codes, teachers)
        sync_enroll_course(request.user, existed_courses_ids, term)

    courses = get_course_list_queryset(request.user)
    courses = courses.filter(enrollcourse__user=request.user)
    serializer = CourseListSerializer(courses, many=True)
    return Response(serializer.data)


class EnrollCourseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseListSerializer
    pagination_class = None

    def get_queryset(self):
        courses = get_course_list_queryset(self.request.user)
        return courses.filter(enrollcourse__user=self.request.user)
