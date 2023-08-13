import jieba
from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class JcourseApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jcourse_api'
    verbose_name = '选课社区'

    def ready(self):
        jieba.initialize()

        from jcourse_api.models import ReviewReaction, Review, Report
        from jcourse_api.signals import signal_delete_review_actions, \
            signal_delete_course_reviews, signal_notify_report_replied
        post_delete.connect(signal_delete_review_actions, sender=ReviewReaction)
        post_delete.connect(signal_delete_course_reviews, sender=Review)
        post_save.connect(signal_notify_report_replied, sender=Report)
        # post_save.connect(signal_notify_new_review_generated, sender=Review)
