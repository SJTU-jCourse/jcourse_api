from django.db import models
from django.utils import timezone


class Touchpoint(models.Model):
    class Meta:
        verbose_name = '触点'
        verbose_name_plural = verbose_name

    name = models.CharField(verbose_name='名称', max_length=64, unique=True)

    def __str__(self):
        return self.name


class Promotion(models.Model):
    class Meta:
        verbose_name = '推广内容'
        verbose_name_plural = verbose_name

    touchpoint = models.ForeignKey(Touchpoint, verbose_name='触点', on_delete=models.DO_NOTHING,
                                   db_index=True, null=True, blank=True)
    image = models.FileField(verbose_name='图片地址', null=True, blank=True)
    text = models.TextField(verbose_name='展示文字', null=True, blank=True)
    jump_link = models.URLField(verbose_name='跳转链接', null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='创建时间', default=timezone.now, db_index=True)
    available = models.BooleanField(verbose_name='启用', default=False, db_index=True)
    description = models.TextField(verbose_name='描述', null=True, blank=True)
