from collections import OrderedDict

from django.db import IntegrityError
from django.db.models import F
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
    class Meta:
        model = Teacher
        fields = ('tid', 'name')


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
    class Meta:
        model = Category
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


def get_course_rating(obj: Course):
    return {'count': obj.review_count, 'avg': obj.review_avg}


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
    rating = serializers.SerializerMethodField()
    related_teachers = serializers.SerializerMethodField()
    related_courses = serializers.SerializerMethodField()
    former_codes = serializers.SerializerMethodField()
    semester = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        exclude = ['review_count', 'review_avg']

    @staticmethod
    def get_former_codes(obj: Course):
        return FormerCode.objects.filter(new_code=obj.code).values_list('old_code', flat=True)

    @staticmethod
    def get_rating(obj: Course):
        return get_course_rating(obj)

    @staticmethod
    def get_related_teachers(obj: Course):
        return Course.objects.filter(code=obj.code).exclude(main_teacher=obj.main_teacher) \
            .values('id', avg=F('review_avg'), count=F('review_count'),
                    tname=F('main_teacher__name')).order_by(F('avg').desc(nulls_last=True))

    @staticmethod
    def get_related_courses(obj: Course):
        return Course.objects.filter(main_teacher=obj.main_teacher).exclude(code=obj.code) \
            .values('id', 'code', 'name', avg=F('review_avg'),
                    count=F('review_count')).order_by(F('avg').desc(nulls_last=True))

    @staticmethod
    def get_semester(obj):
        return obj.semester

    @staticmethod
    def get_is_reviewed(obj):
        return obj.is_reviewed if obj.is_reviewed else None


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
        exclude = ['teacher_group', 'main_teacher', 'moderator_remark', 'review_count', 'review_avg']

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


class CourseInReviewSerializer(serializers.ModelSerializer):
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


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        exclude = ['moderator_remark', 'approve_count', 'disapprove_count']
        read_only_fields = ['user', 'created']

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            error_msg = {'error': '已经点评过这门课，如需修改请联系管理员'}
            raise serializers.ValidationError(error_msg)


def get_review_actions(obj):
    return {'approves': obj.approve_count, 'disapproves': obj.disapprove_count, 'action': obj.my_action}


def is_my_review(serializer: serializers.Serializer, obj: Review):
    request = serializer.context.get("request")
    if request and hasattr(request, "user"):
        user = request.user
        return obj.user_id == user.id
    return False


class ReviewSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField(read_only=True)
    actions = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Review
        exclude = ['user', 'approve_count', 'disapprove_count']

    def get_is_mine(self, obj: Review):
        return is_my_review(self, obj)

    @staticmethod
    def get_actions(obj):
        return get_review_actions(obj)

    @staticmethod
    def get_course(obj):
        serializer = CourseInReviewSerializer(obj.course, context={'semester': obj.my_enroll_semester})
        return serializer.data


class ReviewInCourseSerializer(serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Review
        exclude = ('user', 'course', 'approve_count', 'disapprove_count')

    @staticmethod
    def get_actions(obj):
        return get_review_actions(obj)

    def get_is_mine(self, obj: Review):
        return is_my_review(self, obj)
