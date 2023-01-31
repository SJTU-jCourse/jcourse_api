from django.contrib.auth.models import User
from rest_framework import serializers

from jcourse_api.models import Teacher, Semester, Announcement, Report, Notification, Category, Department, UserPoint


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ('tid', 'name')


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ('id', 'name', 'available')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_staff')


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ('title', 'message', 'created_at', 'url')


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        exclude = ('solved',)
        read_only_fields = ('user', 'created_at', 'reply')


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'recipient', 'type', 'description', 'created_at', 'read_at')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

    count = serializers.SerializerMethodField()

    @staticmethod
    def get_count(obj):
        return obj.count


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

    count = serializers.SerializerMethodField()

    @staticmethod
    def get_count(obj):
        return obj.count


class UserPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPoint
        exclude = ('user', 'id')
