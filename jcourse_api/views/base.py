from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jcourse_api.models import *
from jcourse_api.serializers import SemesterSerializer, CategorySerializer, DepartmentSerializer


class SemesterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Semester.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = SemesterSerializer
    pagination_class = None

    @method_decorator(cache_page(60))
    def dispatch(self, request: Request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class CourseFilterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        categories = Category.objects.annotate(count=Count('course')).filter(count__gt=0)
        category_serializer = CategorySerializer(categories, many=True)
        departments = Department.objects.annotate(count=Count('course')).filter(count__gt=0)
        department_serializer = DepartmentSerializer(departments, many=True)
        return Response({'categories': category_serializer.data, 'departments': department_serializer.data},
                        status=status.HTTP_200_OK)
