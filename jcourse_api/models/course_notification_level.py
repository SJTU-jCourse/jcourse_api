from django.contrib.auth.models import User
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone

from jcourse_api.models import Course, send_course_new_review_notification


class CourseNotificationLevel(models.Model):
    class Meta:
        verbose_name = '课程通知等级'
        verbose_name_plural = verbose_name
        UniqueConstraint(fields=['course', 'user'], name='unique_course_user')

    class NotificationLevelType(models.IntegerChoices):
        NORMAL = 0, '正常'
        FOLLOW = 1, '关注'
        IGNORE = 2, '忽略'

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', db_index=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='课程', db_index=True, blank=True)
    notification_level = models.IntegerField(verbose_name='通知等级', choices=NotificationLevelType.choices,
                                             default=NotificationLevelType.NORMAL, blank=True)
    modified_at = models.DateTimeField(verbose_name='改动时间', default=timezone.now)

    def __str__(self):
        return f"{self.user}-{self.get_notification_level_display()}-{self.course}"


def find_course_new_review(course: Course):
    for course_notification_level in CourseNotificationLevel.objects.filter(
            course=course,
            notification_level=CourseNotificationLevel.NotificationLevelType.FOLLOW
    ):
        send_course_new_review_notification(course_notification_level.user, course)
