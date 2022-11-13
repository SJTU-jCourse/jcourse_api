from rest_framework import serializers

from jcourse_api.models import Review, Course
from jcourse_api.serializers import CourseInReviewListSerializer


class CourseFollowListSerializer(serializers.ModelSerializer):
    course = CourseInReviewListSerializer()

    class Meta:
        model = Course
        fields = ['course', ]


class ReviewFollowListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['user', 'course', 'comment', 'created', 'modified']
