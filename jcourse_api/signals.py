from jcourse_api.models import *


def signal_delete_review_actions(sender, instance: Action, **kwargs):
    update_review_actions(instance.review)


def signal_delete_course_reviews(sender, instance: Review, **kwargs):
    update_course_reviews(instance.course)


def signal_delete_filter_count(sender, instance: Course, **kwargs):
    if instance.category_id is not None:
        update_category_count(instance.category)
    if instance.department_id is not None:
        update_department_count(instance.department)
