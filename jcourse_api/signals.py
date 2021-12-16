from jcourse_api.models import *


def signal_delete_review_actions(sender, instance, **kwargs):
    update_review_actions(instance)


def signal_delete_course_reviews(sender, instance, **kwargs):
    update_course_reviews(instance)


def signal_delete_filter_count(sender, instance, **kwargs):
    if instance.category_id is not None:
        update_category_count(instance)
    if instance.department_id is not None:
        update_department_count(instance)
