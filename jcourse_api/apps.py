from django.apps import AppConfig
from django.db.models.signals import post_delete


class JcourseApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jcourse_api'
    verbose_name = '选课社区'

    def ready(self):
        from jcourse_api.models import ReviewReaction, Review
        from jcourse_api.signals import signal_delete_review_actions, \
            signal_delete_course_reviews
        post_delete.connect(signal_delete_review_actions, sender=ReviewReaction)
        post_delete.connect(signal_delete_course_reviews, sender=Review)
