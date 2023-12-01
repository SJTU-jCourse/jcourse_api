from django.contrib.auth.models import User
from django.db.models import Sum

from jcourse_api.models import Review, UserPoint


def get_user_point_with_reviews(user: User, reviews):
    courses = reviews.values_list('course', flat=True)
    approves_count = reviews.aggregate(count=Sum('approve_count'))['count']
    if approves_count is None:
        approves_count = 0
    reviews_count = reviews.count()

    first_reviews = Review.objects.filter(course__in=courses).order_by('course_id', 'created_at').distinct(
        'course_id').values_list('id', flat=True)
    first_reviews = first_reviews.intersection(reviews)
    first_reviews_count = first_reviews.count()
    first_reviews_approves_count = Review.objects.filter(pk__in=first_reviews).aggregate(count=Sum('approve_count'))[
        'count']
    if first_reviews_approves_count is None:
        first_reviews_approves_count = 0
    additional = UserPoint.objects.filter(user=user)
    additional_point = additional.aggregate(sum=Sum('value'))['sum']
    if additional_point is None:
        additional_point = 0
    points = additional_point + approves_count + first_reviews_approves_count + reviews_count + first_reviews_count
    return points, additional_point
