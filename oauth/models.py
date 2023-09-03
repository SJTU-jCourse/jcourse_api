from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class UserProfile(models.Model):
    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False, blank=False)
    user_type = models.CharField(verbose_name='用户类型', max_length=50, null=True, blank=True)
    lowercase = models.BooleanField(verbose_name='转小写', null=False, default=False)
    suspended_till = models.DateTimeField(verbose_name='封禁到', db_index=True, blank=True, default=None, null=True)
    last_seen_at = models.DateTimeField(verbose_name='活跃时间', db_index=True, blank=True, default=None, null=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        self.sync_suspended_status()

    def sync_suspended_status(self):
        self.user.is_active = (self.suspended_till is None)
        self.user.save(update_fields=['is_active'])
