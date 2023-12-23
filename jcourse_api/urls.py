from django.urls import include, path
from rest_framework.routers import DefaultRouter

from jcourse_api.views import *
from jcourse_api.views.common import get_common_info

router = DefaultRouter()
router.register('course', CourseViewSet, basename='course')
router.register('review', ReviewViewSet, basename='review')
router.register('semester', SemesterViewSet, basename='semester')
router.register('course-in-review', CourseInReviewViewSet, basename='course-in-review')
router.register('announcement', AnnouncementViewSet, basename='announcement')
router.register('search', SearchViewSet, basename='search')
router.register('lesson', EnrollCourseViewSet, basename='lesson')
router.register('report', ReportViewSet, basename='report')
router.register('notification', NotificationViewSet, basename='notification')


urlpatterns = [
    path('', include(router.urls)),
    path('me/', UserView.as_view(), name='me'),
    path('course-filter/', CourseFilterView.as_view(), name='course-filter'),
    path('review-filter/', ReviewFilterView.as_view(), name='review-filter'),
    path('statistic/', StatisticView.as_view(), name='statistic'),
    path('points/', UserPointView.as_view(), name='user-points'),
    path('sync-lessons/<str:term>/', sync_lessons, name='sync-lessons'),
    path('sync-lessons/', sync_lessons, name='sync-lessons'),
    path('sync-lessons-v2/', sync_lessons_v2, name='sync-lessons-v2'),
    path('course/<int:course_id>/review/', ReviewInCourseView.as_view(), name='review-in-course'),
    path('review/<int:review_id>/revision/', ReviewRevisionView.as_view(), name='review-revision'),
    path('common/', get_common_info, name='common-info'),
    path('debug/', debug_info, name='debug-info'),
    # path('upload/', FileUploadView.as_view(), name='upload'),
]
