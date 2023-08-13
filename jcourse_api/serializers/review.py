from django.db import IntegrityError
from rest_framework import serializers

from jcourse_api.models import Review, ReviewRevision
from jcourse_api.serializers.base import SemesterSerializer
from jcourse_api.serializers.course import CourseInReviewListSerializer, CourseInWriteReviewSerializer


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        exclude = ['moderator_remark', 'approve_count', 'disapprove_count', 'search_vector']
        read_only_fields = ['user', 'created_at', 'modified_at']

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            error_msg = {'error': '已经点评过这门课，如需修改，请从“修改点评”入口进入'}
            raise serializers.ValidationError(error_msg)


def get_review_reactions(obj):
    reactions = {'approves': obj.approve_count, 'disapproves': obj.disapprove_count}
    if hasattr(obj, "my_reaction"):
        reactions["reaction"] = obj.my_reaction
    return reactions


def is_my_review(serializer: serializers.Serializer, obj: Review):
    request = serializer.context.get("request")
    if request and hasattr(request, "user"):
        user = request.user
        return obj.user_id == user.id
    return False


class ReviewCommonSerializer(serializers.ModelSerializer):
    reactions = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    semester = serializers.SerializerMethodField()

    class Meta:
        model = Review

    @staticmethod
    def get_semester(obj):
        return obj.semester.name

    def get_is_mine(self, obj: Review):
        return is_my_review(self, obj)

    @staticmethod
    def get_reactions(obj):
        return get_review_reactions(obj)


class ReviewListSerializer(ReviewCommonSerializer):
    course = CourseInReviewListSerializer(read_only=True)

    class Meta:
        model = Review
        exclude = ['user', 'approve_count', 'disapprove_count', 'search_vector']


class ReviewItemSerializer(ReviewCommonSerializer):
    course = serializers.SerializerMethodField()
    semester = SemesterSerializer()

    class Meta:
        model = Review
        exclude = ['user', 'approve_count', 'disapprove_count', 'search_vector']

    @staticmethod
    def get_course(obj):
        serializer = CourseInWriteReviewSerializer(obj.course)
        return serializer.data


class ReviewInCourseSerializer(ReviewCommonSerializer):
    class Meta:
        model = Review
        exclude = ('user', 'course', 'approve_count', 'disapprove_count', 'search_vector')


class ReviewRevisionSerializer(serializers.ModelSerializer):
    semester = serializers.SerializerMethodField()
    course = CourseInWriteReviewSerializer()

    @staticmethod
    def get_semester(obj):
        return obj.semester.name

    class Meta:
        model = ReviewRevision
        exclude = ('review', 'user')
