import django_filters
from django.db.models import Q, Count, Sum
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django_filters import BaseInFilter, NumberFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from jcourse_api.serializers import *
from oauth.views import hash_username, jaccount


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class CourseFilter(django_filters.FilterSet):
    category = NumberInFilter(field_name="category", lookup_expr="in")
    department = NumberInFilter(field_name="department", lookup_expr="in")

    class Meta:
        model = Course
        fields = ['category', 'department']


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CourseFilter

    def get_queryset(self):
        if 'onlyhasreviews' in self.request.query_params:
            courses = Course.objects.filter(review_count__gt=0).annotate(count=F('review_count'), avg=F('review_avg'))
            if self.request.query_params['onlyhasreviews'] == 'count':
                return courses.order_by(F('count').desc(nulls_last=True), F('avg').desc(nulls_last=True))
            return courses.order_by(F('avg').desc(nulls_last=True), F('count').desc(nulls_last=True))
        return Course.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        else:
            return CourseSerializer

    @action(detail=True)
    def review(self, request, pk=None):
        reviews = Review.objects.filter(course_id=pk)
        serializer = ReviewInCourseSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)


def get_search_course_queryset(viewset):
    q = viewset.request.query_params.get('q', '')
    if q == '':
        return Course.objects.none()
    queryset = Course.objects.filter(
        Q(code__icontains=q) | Q(name__icontains=q) | Q(main_teacher__name__icontains=q) |
        Q(main_teacher__pinyin__icontains=q) | Q(main_teacher__abbr_pinyin__icontains=q))
    return queryset


class SearchViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseListSerializer

    def get_queryset(self):
        return get_search_course_queryset(self)


class ReviewInCourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Review.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewInCourseSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return CreateReviewSerializer
        else:
            return ReviewSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['POST'])
    def reaction(self, request, pk=None):
        review = Review.objects.get(pk=pk)
        Action.objects.update_or_create(user=request.user, review_id=pk,
                                        defaults={'action': request.data.get('action')})
        return Response({'id': pk,
                         'action': request.data.get('action'),
                         'approves': review.approve_count,
                         'disapproves': review.disapprove_count},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def mine(self, request):
        reviews = self.queryset.filter(user=request.user)
        serializer = self.get_serializer_class()
        data = serializer(reviews, many=True, context={'request': request}).data
        return Response(data)


class SemesterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Semester.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = SemesterSerializer
    pagination_class = None

    @method_decorator(cache_page(60 * 60 * 2))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class NoticeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notice.objects.filter(available=True)
    permission_classes = [IsAuthenticated]
    serializer_class = NoticeSerializer
    pagination_class = None


class CourseInReviewViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseInReviewSerializer
    pagination_class = None

    def get_queryset(self):
        return get_search_course_queryset(self)


class ReportViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    queryset = Report.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer
    pagination_class = None

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取当前用户信息
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FilterView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60 * 5))
    def get(self, request):
        categories = Category.objects.annotate(count=Count('course')).filter(count__gt=0)
        category_serializer = CategorySerializer(categories, many=True)
        departments = Department.objects.annotate(count=Count('course')).filter(count__gt=0)
        department_serializer = DepartmentSerializer(departments, many=True)
        return Response({'categories': category_serializer.data, 'departments': department_serializer.data},
                        status=status.HTTP_200_OK)


class StatisticView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60 * 5))
    def get(self, request):
        return Response({'courses': Course.objects.count(),
                         'users': User.objects.count(),
                         'reviews': Review.objects.count()},
                        status=status.HTTP_200_OK)


def get_user_point(user: User):
    reviews = Review.objects.filter(user=user)
    courses = reviews.values_list('course', flat=True)
    approve_count = reviews.aggregate(count=Sum('approve_count'))['count']
    if approve_count is None:
        approve_count = 0
    review_count = reviews.count()

    first_reviews = Review.objects.filter(course__in=courses).order_by('course_id', 'created').distinct(
        'course_id').values_list('id', flat=True)
    first_reviews = first_reviews.intersection(reviews)
    first_reviews_count = first_reviews.count()
    first_reviews_approve_count = Review.objects.filter(pk__in=first_reviews).aggregate(count=Sum('approve_count'))[
        'count']
    if first_reviews_approve_count is None:
        first_reviews_approve_count = 0
    points = (approve_count + first_reviews_approve_count) * 2 + review_count + first_reviews_count
    return {'points': points}


@api_view(['POST'])
@csrf_exempt
def user_points(request):
    account = request.data.get('account', '')
    apikey = request.headers.get('Api-Key', '')
    if account == '' or apikey == '':
        return Response({'detail': 'Bad arguments'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ApiKey.objects.get(key=apikey, is_enabled=True)
    except ApiKey.DoesNotExist:
        return Response({'detail': 'Bad arguments'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(username=hash_username(account))
    except User.DoesNotExist:
        return Response({'detail': 'Bad arguments'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(get_user_point(user))


@api_view(['POST'])
def sync_lessons(request, term='2018-2019-2'):
    token = request.session.get('token', None)
    if token is None:
        return Response({'detail': '未授权获取课表信息'}, status=status.HTTP_401_UNAUTHORIZED)
    resp = jaccount.get(f'v1/me/lessons/{term}/', token=token, params={"classes": False}).json()
    codes = []
    teachers = []
    for entity in resp['entities']:
        codes.append(entity['course']['code'])
        teachers.append(entity['teachers'][0]['name'])
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
    existed_courses = Course.objects.filter(conditions).values('id')
    try:
        semester = Semester.objects.get(name=term)
    except Semester.DoesNotExist:
        semester = None
    enroll_courses = []
    for course in existed_courses:
        enroll_courses.append(EnrollCourse(user=request.user, course_id=course['id'], semester=semester))
    EnrollCourse.objects.bulk_create(enroll_courses, ignore_conflicts=True)
    courses = Course.objects.filter(enrollcourse__user=request.user)
    serializer = CourseListSerializer(courses, many=True)
    return Response(serializer.data)


class EnrollCourseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseListSerializer
    pagination_class = None

    def get_queryset(self):
        return Course.objects.filter(enrollcourse__user=self.request.user)
