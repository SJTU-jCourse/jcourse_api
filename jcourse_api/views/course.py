import django_filters
from django.db.models import Subquery, F, OuterRef
from django_filters import BaseInFilter, NumberFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from jcourse_api.models import *
from jcourse_api.serializers import CourseListSerializer, CourseSerializer, CourseInWriteReviewSerializer


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class CourseFilter(django_filters.FilterSet):
    categories = NumberInFilter(field_name="categories", lookup_expr="in")
    department = NumberInFilter(field_name="department", lookup_expr="in")

    class Meta:
        model = Course
        fields = ['categories', 'department']


def get_course_list_queryset(user: User):
    my_review = Review.objects.filter(user=user, course_id=OuterRef('pk')).values('pk')
    my_enroll_semester = EnrollCourse.objects.filter(user=user, course_id=OuterRef('pk')).values('semester')

    return Course.objects.select_related('main_teacher').prefetch_related('categories', 'department').annotate(
        semester=Subquery(my_enroll_semester[:1]),
        is_reviewed=Subquery(my_review[:1]))


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CourseFilter

    def get_queryset(self):
        courses = get_course_list_queryset(self.request.user)
        if 'notification_level' in self.request.query_params:
            notification_level = int(self.request.query_params['notification_level'])
            filtered_course_ids = CourseNotificationLevel.objects.filter(user=self.request.user,
                                                                         notification_level=notification_level) \
                .values('course_id')
            courses = courses.filter(id__in=filtered_course_ids)
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

    # def get_
    @action(detail=True, methods=['POST'])
    def notification_level(self, request: Request, pk=None):
        if 'level' not in request.data:
            return Response({'error': '未指定操作类型！'}, status=status.HTTP_400_BAD_REQUEST)
        # if pk is None:
        #     return Response({'error': '未指定课程id！'}, status=status.HTTP_400_BAD_REQUEST)
        notification_level = int(request.data['level'])
        if notification_level not in CourseNotificationLevel.NotificationLevelType:
            return Response({'error': '无效的操作类型！'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course = Course.objects.get(id=pk)
            course_notification, find = CourseNotificationLevel.objects.update_or_create(
                user=request.user,
                course=course,
                defaults={'notification_level': notification_level}
            )
        except Course.DoesNotExist:
            return Response({'error': '无指定课程！'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'id': pk,
                         'notification_level': course_notification.notification_level},
                        status=status.HTTP_200_OK)


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


class CourseInReviewViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseInWriteReviewSerializer

    def get_queryset(self):
        if self.action == 'list':
            q = self.request.query_params.get('q', '')
            return get_search_course_queryset(q, self.request.user)
        elif self.action == 'retrieve':
            return get_course_list_queryset(self.request.user)
