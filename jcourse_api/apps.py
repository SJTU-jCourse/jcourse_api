from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class JcourseApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jcourse_api'
    verbose_name = '选课社区'

    def ready(self):
        from jcourse_api.models import Action, Review, Course
        from jcourse_api.signals import update_review_actions, update_course_reviews, update_filter_count
        post_save.connect(update_review_actions, sender=Action)
        post_delete.connect(update_review_actions, sender=Action)
        post_save.connect(update_course_reviews, sender=Review)
        post_delete.connect(update_course_reviews, sender=Review)
        post_save.connect(update_filter_count, sender=Course)
        post_delete.connect(update_filter_count, sender=Course)
