from django.db import models
from django.db.models import UniqueConstraint, Q
from django.utils import timezone

from ad.storage import QiniuStorage


class Promotion(models.Model):
    class TouchPointType(models.IntegerChoices):
        BELOW_RELATED_COURSE = 1, '更多课程下方'

    class Meta:
        verbose_name = '推广内容'
        verbose_name_plural = verbose_name
        constraints = [
            UniqueConstraint(fields=["touchpoint"], condition=Q(available=True), name="touchpoint_one_online")]

    touchpoint = models.IntegerField(choices=TouchPointType.choices, verbose_name='触点',
                                     db_index=True, null=True, blank=True)
    image = models.ImageField(verbose_name='内部图片', null=True, blank=True, storage=QiniuStorage(child_name='upload'))
    external_image = models.URLField(verbose_name='外部图片地址', null=True, blank=True)
    text = models.TextField(verbose_name='展示文字', null=True, blank=True)
    jump_link = models.URLField(verbose_name='跳转链接', null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='创建时间', default=timezone.now, db_index=True)
    available = models.BooleanField(verbose_name='启用', default=False, db_index=True)
    description = models.TextField(verbose_name='描述', null=True, blank=True)
    click_times = models.IntegerField(verbose_name='点击次数', default=0, null=False, blank=False)
