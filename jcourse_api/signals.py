from django.db.models import Count, Avg, Q

from jcourse_api.models import Action, Review


def update_review_actions(sender, **kwargs):
    action = kwargs['instance']
    review = action.review
    actions = Action.objects.filter(review=review).aggregate(approves=Count('action', filter=Q(action=1)),
                                                             disapproves=Count('action', filter=Q(action=-1)))
    review.approve_count = actions['approves']
    review.disapprove_count = actions['disapproves']
    review.save()


def update_course_reviews(sender, **kwargs):
    review = kwargs['instance']
    course = review.course
    review = Review.objects.filter(course=course).aggregate(avg=Avg('rating'), count=Count('*'))
    course.review_count = review['count']
    course.review_avg = review['avg']
    course.save()
