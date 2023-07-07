from django.db.models import F
from rest_framework import serializers

from jcourse_api.models import Course, Department, Category, FormerCode, CourseNotificationLevel
from jcourse_api.serializers.base import TeacherSerializer


def get_course_rating(obj: Course):
    return {'count': obj.review_count, 'avg': obj.review_avg}


class CourseSerializer(serializers.ModelSerializer):
    categories = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        many=True,
        required=False,
        slug_field='name'
    )
    department = serializers.SlugRelatedField(
        queryset=Department.objects.all(),
        many=False,
        required=False,
        slug_field='name'
    )
    main_teacher = TeacherSerializer(read_only=True)
    teacher_group = TeacherSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()
    related_teachers = serializers.SerializerMethodField()
    related_courses = serializers.SerializerMethodField()
    semester = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()
    notification_level = serializers.SerializerMethodField()

    class Meta:
        model = Course
        exclude = ['review_count', 'review_avg', 'last_semester']

    @staticmethod
    def get_rating(obj: Course):
        return get_course_rating(obj)

    @staticmethod
    def get_related_teachers(obj: Course):
        return Course.objects.filter(code=obj.code).exclude(main_teacher=obj.main_teacher) \
            .values('id', avg=F('review_avg'), count=F('review_count'),
                    tname=F('main_teacher__name')).order_by(F('avg').desc(nulls_last=True),
                                                            F('count').desc(nulls_last=True))

    @staticmethod
    def get_related_courses(obj: Course):
        return Course.objects.filter(main_teacher=obj.main_teacher).exclude(code=obj.code) \
            .values('id', 'code', 'name', avg=F('review_avg'),
                    count=F('review_count')).order_by(F('avg').desc(nulls_last=True), F('count').desc(nulls_last=True))

    @staticmethod
    def get_semester(obj):
        return obj.semester

    @staticmethod
    def get_is_reviewed(obj):
        return obj.is_reviewed if obj.is_reviewed else None

    def get_notification_level(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            try:
                return CourseNotificationLevel.objects.get(user=request.user, course_id=obj.id).notification_level
            except CourseNotificationLevel.DoesNotExist:
                return None
        return None


class CourseListSerializer(serializers.ModelSerializer):
    categories = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        many=True,
        required=False,
        slug_field='name'
    )
    department = serializers.SlugRelatedField(
        queryset=Department.objects.all(),
        many=False,
        required=False,
        slug_field='name'
    )
    teacher = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()
    semester = serializers.SerializerMethodField()

    class Meta:
        model = Course
        exclude = ['teacher_group', 'main_teacher', 'moderator_remark', 'review_count', 'review_avg', 'last_semester']

    @staticmethod
    def get_rating(obj: Course):
        return get_course_rating(obj)

    @staticmethod
    def get_teacher(obj: Course):
        return obj.main_teacher.name

    @staticmethod
    def get_is_reviewed(obj):
        return obj.is_reviewed if obj.is_reviewed else None

    @staticmethod
    def get_semester(obj):
        return obj.semester


class CourseInReviewListSerializer(serializers.ModelSerializer):
    teacher = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'code', 'name', 'teacher']

    @staticmethod
    def get_teacher(obj: Course):
        return obj.main_teacher.name


class CourseInWriteReviewSerializer(serializers.ModelSerializer):
    teacher = serializers.SerializerMethodField()
    semester = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'code', 'name', 'teacher', 'semester']

    @staticmethod
    def get_teacher(obj: Course):
        return obj.main_teacher.name

    def get_semester(self, obj):
        if hasattr(obj, 'semester'):
            semester = obj.semester
        else:
            semester = self.context.get('semester', None)
        return semester
