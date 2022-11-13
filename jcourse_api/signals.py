from jcourse_api.models import *


def signal_delete_review_actions(sender, instance: ReviewReaction, **kwargs):
    update_review_reactions(instance.review)


def signal_delete_course_reviews(sender, instance: Review, **kwargs):
    update_course_reviews(instance.course)


def signal_notify_report_replied(sender, instance: Report, **kwargs):
    send_report_replied_notification(instance)


def signal_notify_new_review_generated(sender, instance: Review, **kwargs):
    find_course_new_review(instance.course)
