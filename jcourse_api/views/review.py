from django.db import transaction
from django.db.models import Subquery, OuterRef, F
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from jcourse import settings
from jcourse.throttles import ReactionRateThrottle
from jcourse_api.models import *
from jcourse_api.permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from jcourse_api.serializers import ReviewRevisionSerializer, CreateReviewSerializer, ReviewItemSerializer, \
    ReviewListSerializer, ReviewInCourseSerializer


def get_reviews(user: User, action: str):
    my_reaction = ReviewReaction.objects.filter(user=user, review_id=OuterRef('pk')).values('reaction')
    reviews = Review.objects.select_related('course', 'course__main_teacher', 'semester')
    if action == 'retrieve':
        my_enroll_semester = EnrollCourse.objects.filter(user=user, course_id=OuterRef('course_id')).values('semester')
        return reviews.annotate(
            my_reaction=Subquery(my_reaction[:1]), my_enroll_semester=Subquery(my_enroll_semester[:1]))
    return reviews.annotate(my_reaction=Subquery(my_reaction[:1]))


class ReviewViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        if settings.REVIEW_READ_ONLY:
            return [IsAdminOrReadOnly()]
        else:
            return [IsOwnerOrReadOnly()]

    def get_queryset(self):
        reviews = get_reviews(self.request.user, self.action)
        if 'order' in self.request.query_params:
            if self.request.query_params['order'] == 'approves':
                return reviews.order_by(F('approve_count').desc(nulls_last=True), F('created').desc(nulls_last=True))
        return reviews

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return CreateReviewSerializer
        elif self.action == 'retrieve':
            return ReviewItemSerializer
        else:
            return ReviewListSerializer

    def perform_create(self, serializer: serializers.ModelSerializer):
        created_time = timezone.now()
        serializer.save(user=self.request.user, modified=created_time, created=created_time)

    def perform_update(self, serializer: serializers.ModelSerializer):
        modified_time = timezone.now()
        review: Review = serializer.instance
        with transaction.atomic():
            ReviewRevision.objects.create(user=self.request.user,
                                          review_id=review.id, course_id=review.course_id,
                                          semester_id=review.semester_id, score=review.score,
                                          rating=review.rating, comment=review.comment,
                                          created=modified_time, )
            serializer.save(modified=modified_time)

    @action(detail=True, methods=['POST'], throttle_classes=[UserRateThrottle, ReactionRateThrottle])
    def reaction(self, request: Request, pk=None):
        if 'reaction' not in request.data:
            return Response({'error': '未指定操作类型！'}, status=status.HTTP_400_BAD_REQUEST)
        if pk is None:
            return Response({'error': '未指定点评id！'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            ReviewReaction.objects.update_or_create(user=request.user, review_id=pk,
                                                    defaults={'reaction': request.data.get('reaction')})
            review = Review.objects.get(pk=pk)
        except (ReviewReaction.DoesNotExist, Review.DoesNotExist):
            return Response({'error': '无指定点评！'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'id': pk,
                         'reaction': request.data.get('reaction'),
                         'approves': review.approve_count,
                         'disapproves': review.disapprove_count},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def mine(self, request: Request):
        reviews = get_reviews(self.request.user, 'list').filter(user=request.user)
        serializer = self.get_serializer_class()
        data = serializer(reviews, many=True, context={'request': request}).data
        return Response(data)


class ReviewRevisionView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ReviewRevisionSerializer
    lookup_url_kwarg = 'review_id'

    def get_queryset(self):
        review_id = self.kwargs.get('review_id')
        return ReviewRevision.objects.select_related('semester').filter(review_id=review_id).order_by(
            F('created').desc(nulls_last=True))


class ReviewInCourseView(ListAPIView):
    lookup_url_kwarg = 'course_id'
    serializer_class = ReviewInCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        pk = self.kwargs.get('course_id')
        return get_reviews(self.request.user, 'list').select_related('semester').filter(course_id=pk)
