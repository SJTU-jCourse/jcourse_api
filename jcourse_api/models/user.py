from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from jcourse_api.models import Course, Semester, constrain_text


class EnrollCourse(models.Model):
    class Meta:
        verbose_name = '选课记录'
        verbose_name_plural = verbose_name
        constraints = [models.UniqueConstraint(fields=['user', 'course', 'semester'], name='unique_enroll')]

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE, db_index=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_index=True)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='创建时间', default=timezone.now, db_index=True)

    def __str__(self):
        return f"{self.user} {self.course.name} {self.semester.name}"


class UserPoint(models.Model):
    class Meta:
        verbose_name = '积分'
        verbose_name_plural = verbose_name

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE, db_index=True)
    value = models.IntegerField(verbose_name='数值', default=0, null=False)
    description = models.CharField(verbose_name='原因', max_length=255, null=True)
    time = models.DateTimeField(verbose_name='时间', default=timezone.now, db_index=True)

    def __str__(self):
        return f"{self.user} 积分：{self.value} 原因：{constrain_text(self.description)}"


class Report(models.Model):
    class Meta:
        verbose_name = '反馈'
        ordering = ['-created_at']
        verbose_name_plural = verbose_name

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE, db_index=True)
    solved = models.BooleanField(verbose_name='是否解决', default=False, db_index=True)
    comment = models.TextField(verbose_name='反馈', max_length=817)
    created_at = models.DateTimeField(verbose_name='发布时间', default=timezone.now, db_index=True)
    reply = models.TextField(verbose_name='回复', max_length=817, null=True, blank=True)

    def __str__(self):
        return f"{self.user}：{constrain_text(self.comment)}"

    def comment_validity(self):
        return constrain_text(self.comment)

    def reply_validity(self):
        return constrain_text(self.reply)

    comment_validity.short_description = '反馈'
    reply_validity.short_description = '回复'
