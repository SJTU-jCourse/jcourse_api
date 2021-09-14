from collections import OrderedDict

from django.db import IntegrityError
from django.db.models import Avg, Count, F, Q, Max
from rest_framework import serializers

from jcourse_api.models import *


class ChoiceDisplayField(serializers.Field):
    """Custom ChoiceField serializer field."""

    def __init__(self, choices, **kwargs):
        """init."""
        self._choices = OrderedDict(choices)
        super(ChoiceDisplayField, self).__init__(**kwargs)

    # 返回可读性良好的字符串而不是 1，-1 这样的数字
    def to_representation(self, obj):
        """Used while retrieving value for the field."""
        return self._choices[obj]

    def to_internal_value(self, data):
        """Used while storing value for the field."""
        for i in self._choices:
            # 这样无论用户POST上来但是CHOICES的 Key 还是Value 都能被接受
            if i == data or self._choices[i] == data:
                return i
        raise serializers.ValidationError("Acceptable values are {0}.".format(list(self._choices.values())))


class TeacherSerializer(serializers.ModelSerializer):
    department = serializers.SlugRelatedField(
        queryset=Department.objects.all(),
        many=False,
        required=False,
        slug_field='name'
    )

    class Meta:
        model = Teacher
        fields = ('tid', 'name', 'department', 'title')


def get_course_rating(obj: Course):
    return Review.objects.filter(course=obj.id, available=True).aggregate(avg=Avg('rating'), count=Count('rating'))


class CourseSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        many=False,
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
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        many=False,
        required=False,
        slug_field='name'
    )
    rating = serializers.SerializerMethodField()
    related_teachers = serializers.SerializerMethodField()
    related_courses = serializers.SerializerMethodField()
    former_codes = serializers.SerializerMethodField()
    semester = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'

    @staticmethod
    def get_former_codes(obj):
        return [i[0] for i in FormerCode.objects.filter(new_code=obj.code).values_list('old_code')]

    @staticmethod
    def get_rating(obj):
        return get_course_rating(obj)

    @staticmethod
    def get_related_teachers(obj):
        return Course.objects.filter(code=obj.code).exclude(main_teacher=obj.main_teacher) \
            .annotate(avg=Avg('review__rating', filter=Q(review__available=True)),
                      count=Count('review__rating', filter=Q(review__available=True))) \
            .values('id', 'avg', 'count', tname=F('main_teacher__name')).order_by(F('avg').desc(nulls_last=True))

    @staticmethod
    def get_related_courses(obj):
        return Course.objects.filter(main_teacher=obj.main_teacher).exclude(code=obj.code) \
            .annotate(avg=Avg('review__rating', filter=Q(review__available=True)),
                      count=Count('review__rating', filter=Q(review__available=True))) \
            .values('id', 'code', 'name', 'avg', 'count').order_by(F('avg').desc(nulls_last=True))

    def get_semester(self, obj):
        return get_enroll_semester(self, obj)


def get_enroll_semester(serializer: serializers.Serializer, obj: Course):
    request = serializer.context.get("request")
    if request and hasattr(request, "user"):
        user = request.user
        try:
            semester = EnrollCourse.objects.get(user=user, course=obj).semester
            if semester is None:
                return None
            semester_serializer = SemesterSerializer(semester, many=False)
            return semester_serializer.data
        except EnrollCourse.DoesNotExist:
            return None
    return None


def is_course_reviewed(serializer: serializers.Serializer, obj: Course):
    request = serializer.context.get("request")
    if request and hasattr(request, "user"):
        user = request.user
        return Review.objects.filter(course=obj.id, user=user).exists()
    return False


class CourseListSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        many=False,
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
        exclude = ['teacher_group', 'language', 'main_teacher', 'moderator_remark']

    @staticmethod
    def get_rating(obj):
        return get_course_rating(obj)

    @staticmethod
    def get_teacher(obj):
        return obj.main_teacher.name

    def get_is_reviewed(self, obj):
        return is_course_reviewed(self, obj)

    def get_semester(self, obj):
        return get_enroll_semester(self, obj)


class CourseInReviewSerializer(serializers.ModelSerializer):
    teacher = serializers.SerializerMethodField()
    semester = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'code', 'name', 'teacher', 'semester']

    @staticmethod
    def get_teacher(obj):
        return obj.main_teacher.name

    def get_semester(self, obj):
        return get_enroll_semester(self, obj)


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        exclude = ['available', 'moderator_remark', ]
        read_only_fields = ['user', 'created']

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            error_msg = {'error': '已经点评过这门课，如需修改请联系管理员'}
            raise serializers.ValidationError(error_msg)


def get_review_actions(serializer: serializers.Serializer, obj: Review):
    request = serializer.context.get("request")
    if request and hasattr(request, "user"):
        user = request.user
        return Action.objects.filter(review=obj).aggregate(approves=Count('pk', filter=Q(action=1)),
                                                           disapproves=Count('pk', filter=Q(action=-1)),
                                                           action=Max('action', filter=Q(user=user)))
    else:
        return Action.objects.filter(review=obj).aggregate(approves=Count('pk', filter=Q(action=1)),
                                                           disapproves=Count('pk', filter=Q(action=-1)))


def is_my_review(serializer: serializers.Serializer, obj: Review):
    request = serializer.context.get("request")
    if request and hasattr(request, "user"):
        user = request.user
        return obj.user == user
    return False


class ReviewSerializer(serializers.ModelSerializer):
    semester = serializers.SlugRelatedField(
        queryset=Semester.objects.all(),
        many=False,
        required=False,
        slug_field='name'
    )
    course = CourseInReviewSerializer(read_only=True)
    actions = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Review
        exclude = ['user', 'available']

    def get_is_mine(self, obj):
        return is_my_review(self, obj)

    def get_actions(self, obj):
        return get_review_actions(self, obj)


class ReviewInCourseSerializer(serializers.ModelSerializer):
    semester = serializers.SlugRelatedField(
        queryset=Semester.objects.all(),
        many=False,
        required=False,
        slug_field='name'
    )
    actions = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Review
        exclude = ('user', 'available', 'course')

    def get_actions(self, obj):
        return get_review_actions(self, obj)

    def get_is_mine(self, obj):
        return is_my_review(self, obj)


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_staff')


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ('title', 'message', 'created')


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        exclude = ('solved',)
        read_only_fields = ('user', 'created', 'reply')


class CategorySerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'

    @staticmethod
    def get_count(obj):
        return Course.objects.filter(category=obj).count()


class DepartmentSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = '__all__'

    @staticmethod
    def get_count(obj):
        return Course.objects.filter(department=obj).count()
