from django.db import models


class Department(models.Model):
    class Meta:
        verbose_name = '教学单位'
        ordering = ['name']
        verbose_name_plural = verbose_name

    name = models.CharField(verbose_name='名称', max_length=64, unique=True)

    def __str__(self):
        return self.name


def constrain_text(text: str) -> str:
    if len(str(text)) > 40:  # 字数自己设置
        return '{}……'.format(str(text)[0:40])  # 超出部分以省略号代替。
    else:
        return str(text)


class Semester(models.Model):
    class Meta:
        verbose_name = '学期'
        verbose_name_plural = verbose_name
        ordering = ['-name']

    name = models.CharField(verbose_name='名称', max_length=64, unique=True)
    available = models.BooleanField(verbose_name='用户可选', default=True)

    def __str__(self):
        return self.name
