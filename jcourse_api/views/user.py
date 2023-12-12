from django.db.models import Sum
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.vary import vary_on_cookie
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jcourse_api.models import *
from jcourse_api.serializers import ReportSerializer, UserSerializer, UserPointSerializer
from jcourse_api.tasks import send_report_email
from oauth.utils import hash_username


class ReportViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = ReportSerializer
    pagination_class = None

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)

    def perform_create(self, serializer: serializer_class):
        serializer.save(user=self.request.user)
        data = serializer.data
        send_report_email(data['comment'], data['created_at'])


class UserView(APIView):

    def get(self, request: Request):
        """
        获取当前用户信息
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


def get_user_point(user: User):
    user_points = UserPoint.objects.filter(user=user)
    points = user_points.aggregate(sum=Sum('value'))['sum']
    if points is None:
        points = 0
    details = UserPointSerializer(user_points, many=True).data
    return {'points': points, 'details': details}


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
