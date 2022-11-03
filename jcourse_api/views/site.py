from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jcourse_api.models import Announcement, Review, Course
from jcourse_api.serializers import AnnouncementSerializer


class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Announcement.objects.filter(available=True)
    permission_classes = [IsAuthenticated]
    serializer_class = AnnouncementSerializer
    pagination_class = None


class StatisticView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60))
    def get(self, request: Request):
        user_join = User.objects.annotate(date=TruncDate("date_joined")).values("date").annotate(
            count=Count("id")).order_by("date")
        review_create = Review.objects.annotate(date=TruncDate("created")).values("date").annotate(
            count=Count("id")).order_by("date")
        return Response({'courses': Course.objects.count(),
                         'courses_with_review': Course.objects.filter(review_count__gt=0).count(),
                         'users': User.objects.count(),
                         'reviews': Review.objects.count(),
                         'user_join': user_join,
                         'review_create': review_create},
                        status=status.HTTP_200_OK)
