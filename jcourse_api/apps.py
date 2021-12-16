from django.apps import AppConfig
from django.db.models.signals import post_delete


class JcourseApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jcourse_api'
    verbose_name = '选课社区'

    def ready(self):
        from jcourse_api.models import Action, Review, Course
        from jcourse_api.signals import signal_delete_review_actions, \
            signal_delete_course_reviews, \
            signal_delete_filter_count
        post_delete.connect(signal_delete_review_actions, sender=Action)
        post_delete.connect(signal_delete_course_reviews, sender=Review)
        post_delete.connect(signal_delete_filter_count, sender=Course)
