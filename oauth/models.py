from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class UserProfile(models.Model):
    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False, blank=False)
    user_type = models.CharField(verbose_name='用户类型', max_length=50, null=True, blank=True)
