import django_filters
from django.db.models import F
from django_filters import BaseInFilter, NumberFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from jcourse_api.models import *
from jcourse_api.repository import get_course_list_queryset, get_search_course_queryset
from jcourse_api.serializers import CourseListSerializer, CourseSerializer, CourseInWriteReviewSerializer


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class CourseFilter(django_filters.FilterSet):
    categories = NumberInFilter(field_name="categories", lookup_expr="in")
    department = NumberInFilter(field_name="department", lookup_expr="in")

    class Meta:
        model = Course
        fields = ['categories', 'department']


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_class = CourseFilter

    def get_queryset(self):
        courses = get_course_list_queryset(self.request.user)
        if 'notification_level' in self.request.query_params:
            notification_level = int(self.request.query_params['notification_level'])
            filtered_course_ids = CourseNotificationLevel.objects.filter(user=self.request.user,
                                                                         notification_level=notification_level) \
                .order_by('modified_at').values('course_id')
            courses = courses.filter(id__in=filtered_course_ids)
        if 'onlyhasreviews' in self.request.query_params:
            courses = courses.filter(review_count__gt=0). \
                annotate(count=F('review_count'), avg=F('review_avg'))
            if self.request.query_params['onlyhasreviews'] == 'count':
                return courses.order_by(F('count').desc(nulls_last=True), F('avg').desc(nulls_last=True), "id")
            return courses.order_by(F('avg').desc(nulls_last=True), F('count').desc(nulls_last=True), "id")
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
        notification_level = int(request.data['level'])
        if notification_level not in CourseNotificationLevel.NotificationLevelType:
            return Response({'error': '无效的操作类型！'}, status=status.HTTP_400_BAD_REQUEST)

        course: Course = self.get_object()
        course_notification, find = CourseNotificationLevel.objects.update_or_create(
            user=request.user,
            course=course,
            defaults={'notification_level': notification_level, 'modified_at': timezone.now()}
        )

        return Response({'id': pk,
                         'notification_level': course_notification.notification_level},
                        status=status.HTTP_200_OK)


class SearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CourseListSerializer

    def get_queryset(self):
        q = self.request.query_params.get('q', '')
        return get_search_course_queryset(q, self.request.user)


class CourseInReviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CourseInWriteReviewSerializer

    def get_queryset(self):
        if self.action == 'list':
            q = self.request.query_params.get('q', '')
            return get_search_course_queryset(q, self.request.user)
        elif self.action == 'retrieve':
            return get_course_list_queryset(self.request.user)
