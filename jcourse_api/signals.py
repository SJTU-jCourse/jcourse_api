from jcourse_api.models import *


def signal_delete_review_actions(sender, instance: ReviewReaction, **kwargs):
    update_review_reactions(instance.review)


def signal_delete_course_reviews(sender, instance: Review, **kwargs):
    update_course_reviews(instance.course)
