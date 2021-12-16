from django.db.models import Count, Avg, Q

from jcourse_api.models import Action, Review, Course


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


def update_filter_count(sender, **kwargs):
    course = kwargs['instance']
    department = course.department
    if department:
        department.count = Course.objects.filter(department=department).count()
        department.save()
    category = course.category
    if category:
        category.count = Course.objects.filter(category=category).count()
        category.save()
