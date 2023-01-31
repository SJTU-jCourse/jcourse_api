from django.core.mail import send_mail
from django.db.models import Sum, F
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.vary import vary_on_cookie
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jcourse import settings
from jcourse_api.models import *
from jcourse_api.serializers import ReportSerializer, UserSerializer, UserPointSerializer
from oauth.views import hash_username


class ReportViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = ReportSerializer
    pagination_class = None

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)

    def perform_create(self, serializer: serializer_class):
        serializer.save(user=self.request.user)
        if not settings.DEBUG:
            data = serializer.data
            email_body = f"内容：\n{data['comment']}\n时间：{data['created_at']}"
            send_mail('选课社区反馈', email_body, from_email=settings.DEFAULT_FROM_EMAIL,
                      recipient_list=[settings.ADMIN_EMAIL])


class UserView(APIView):

    def get(self, request: Request):
        """
        获取当前用户信息
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


def get_user_point_with_reviews(user: User, reviews):
    courses = reviews.values_list('course', flat=True)
    approves_count = reviews.aggregate(count=Sum('approve_count'))['count']
    if approves_count is None:
        approves_count = 0
    reviews_count = reviews.count()

    first_reviews = Review.objects.filter(course__in=courses).order_by('course_id', 'created_at').distinct(
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
        if self.request.method == 'POST':
            return [AllowAny()]
        else:
            return super().get_permissions()

    @method_decorator(cache_page(60))
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
