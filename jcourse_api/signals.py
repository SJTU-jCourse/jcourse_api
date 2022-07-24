from jcourse_api.models import *


def signal_delete_review_actions(sender, instance: Action, **kwargs):
    update_review_actions(instance.review)


def signal_delete_course_reviews(sender, instance: Review, **kwargs):
    update_course_reviews(instance.course)
