from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from jcourse_api.models import Report, Course


class Notification(models.Model):
    class NotificationType(models.IntegerChoices):
        ADMIN_REPLY = 0, '管理员回复'
        GET_LIKES = 1, '获得点赞'
        POINTS_INVALID = 2, '积分失效'
        POINTS_COMPENSATE = 3, '积分补偿'
        REVIEWS_REPLIED = 4, '点评被回复'
        REVIEWS_QUOTED = 5, '点评被引用'
        REVIEWS_REMOVED = 6, '点评被删除'
        REPORTS_REPLIED = 7, '反馈被回复'
        COURSES_NEW_REVIEW = 8, '关注的课程有新点评'

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='接收者',
        db_index=True
    )
    type = models.IntegerField(verbose_name='类型', choices=NotificationType.choices,
                               db_index=True, null=True, blank=True)
    description = models.TextField(blank=True, null=True, verbose_name='内容')
    content_type = models.ForeignKey(ContentType, models.CASCADE, verbose_name='内容类型', null=True)
    object_id = models.PositiveIntegerField(verbose_name='内容ID', null=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='创建时间')
    read_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name='阅读时间')
    public = models.BooleanField(default=True, db_index=True, verbose_name='已发布')

    @admin.display(description='已读', boolean=True)
    def read(self):
        return self.read_at is not None

    def __str__(self):
        return f"{self.id}"


def send_report_replied_notification(report: Report):
    if report.reply:
        Notification.objects.create(
            recipient=report.user,
            type=Notification.NotificationType.REPORTS_REPLIED,
            content_type=ContentType.objects.get_for_model(report),
            object_id=report.id,
            created_at=timezone.now()
        )


def send_course_new_review_notification(user: User, course: Course):
    Notification.objects.create(
        recipient=user,
        type=Notification.NotificationType.COURSES_NEW_REVIEW,
        content_type=ContentType.objects.get_for_model(course),
        object_id=course.id,
        created_at=timezone.now()
    )
