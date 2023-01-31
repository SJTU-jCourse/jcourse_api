from django.db import models
from django.utils import timezone


class Announcement(models.Model):
    class Meta:
        verbose_name = '公告'
        ordering = ['-created_at']
        verbose_name_plural = verbose_name

    title = models.CharField(verbose_name='标题', max_length=256)
    message = models.TextField(verbose_name='正文', max_length=256)
    url = models.TextField(verbose_name='链接', max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='发布时间', default=timezone.now)
    available = models.BooleanField(verbose_name='是否显示', default=True)

    def __str__(self):
        return self.title


class ApiKey(models.Model):
    class Meta:
        verbose_name = 'Api密钥'
        verbose_name_plural = verbose_name

    key = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.CharField(verbose_name='描述', max_length=255)
    is_enabled = models.BooleanField(verbose_name='启用', default=True)
    modified_at = models.DateTimeField(verbose_name='修改时间', default=timezone.now)

    def __str__(self):
        return f"{self.description}：{self.key} - {self.modified_at}"
