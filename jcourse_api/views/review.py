from django.db import transaction
from django.db.models import Subquery, OuterRef, F
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from jcourse import settings
from jcourse.throttles import ReactionRateThrottle
from jcourse_api.models import *
from jcourse_api.permissions import IsAdminOrReadOnly, IsOwnerOrAdminOrReadOnly
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
            return [IsOwnerOrAdminOrReadOnly()]

    def get_queryset(self):
        reviews = get_reviews(self.request.user, self.action)
        if 'notification_level' in self.request.query_params:
            notification_level = int(self.request.query_params['notification_level'])
            filtered_course_ids = CourseNotificationLevel.objects.filter(user=self.request.user,
                                                                         notification_level=notification_level) \
                .values('course_id')
            reviews = reviews.filter(course_id__in=filtered_course_ids)
        else:
            ignored_course_ids = CourseNotificationLevel.objects.filter(user=self.request.user,
                                                                        notification_level=CourseNotificationLevel.NotificationLevelType.IGNORE) \
                .values('course_id')
            reviews = reviews.exclude(course_id__in=ignored_course_ids)
        if 'order' in self.request.query_params:
            if self.request.query_params['order'] == 'approves':
                return reviews.order_by(F('approve_count').desc(nulls_last=True), F('created_at').desc(nulls_last=True))
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
        serializer.save(user=self.request.user, modified_at=created_time, created_at=created_time)

    def perform_update(self, serializer: serializers.ModelSerializer):
        modified_time = timezone.now()
        review: Review = serializer.instance
        with transaction.atomic():
            ReviewRevision.objects.create(user=self.request.user,
                                          review_id=review.id, course_id=review.course_id,
                                          semester_id=review.semester_id, score=review.score,
                                          rating=review.rating, comment=review.comment,
                                          created_at=modified_time, )
            serializer.save(modified_at=modified_time)

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

    @action(detail=True, methods=['GET'])
    def location(self, request, pk):
        review = Review.objects.get(pk=pk)
        location = Review.objects.filter(course_id=review.course_id, modified_at__gt=review.modified_at).count()
        return Response({"location": location, "course": review.course_id})


class ReviewRevisionView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ReviewRevisionSerializer
    lookup_url_kwarg = 'review_id'

    def get_queryset(self):
        review_id = self.kwargs.get('review_id')
        return ReviewRevision.objects.select_related('semester').filter(review_id=review_id).order_by(
            F('created_at').desc(nulls_last=True))


class ReviewInCourseView(ListAPIView):
    lookup_url_kwarg = 'course_id'
    serializer_class = ReviewInCourseSerializer

    class OrderType(models.IntegerChoices):
        LATEST_MODIFIED = 0, '最新发表'
        OLDEST_MODIFIED = 1, '最早发表'
        APPROVE_FROM_HIGH_TO_LOW = 2, '获赞从高到低'
        RATING_FROM_HIGH_TO_LOW = 3, '推荐指数从高到低'
        RATING_FROM_LOW_TO_HIGH = 4, '推荐指数从低到高'

    def get_queryset(self):
        pk = self.kwargs.get('course_id')
        reviews = get_reviews(self.request.user, 'list').select_related('semester').filter(course_id=pk)
        if 'order' in self.request.query_params:
            order = int(self.request.query_params['order'])
            if order not in ReviewInCourseView.OrderType:
                return Review.objects.none()
            if order == ReviewInCourseView.OrderType.LATEST_MODIFIED:
                reviews = reviews.order_by(F('modified_at').desc())
            elif order == ReviewInCourseView.OrderType.OLDEST_MODIFIED:
                reviews = reviews.order_by(F('modified_at').asc())
            elif order == ReviewInCourseView.OrderType.APPROVE_FROM_HIGH_TO_LOW:
                reviews = reviews.order_by(F('approve_count').desc())
            elif order == ReviewInCourseView.OrderType.RATING_FROM_HIGH_TO_LOW:
                reviews = reviews.order_by(F('rating').desc())
            elif order == ReviewInCourseView.OrderType.RATING_FROM_LOW_TO_HIGH:
                reviews = reviews.order_by(F('rating').asc())
        if 'semester' in self.request.query_params:
            semester_id = int(self.request.query_params['semester'])
            reviews = reviews.filter(semester__id=semester_id)
        if 'rating' in self.request.query_params:
            rating = int(self.request.query_params['rating'])
            reviews = reviews.filter(rating=rating)
        return reviews
