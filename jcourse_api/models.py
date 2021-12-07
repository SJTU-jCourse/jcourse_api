from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def constrain_text(text: str) -> str:
    if len(str(text)) > 40:  # 字数自己设置
        return '{}……'.format(str(text)[0:40])  # 超出部分以省略号代替。
    else:
        return str(text)


class Department(models.Model):
    class Meta:
        verbose_name = '教学单位'
        ordering = ['name']
        verbose_name_plural = verbose_name

    name = models.CharField(verbose_name='名称', max_length=64, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    class Meta:
        verbose_name = '课程类别'
        ordering = ['name']
        verbose_name_plural = verbose_name

    name = models.CharField(verbose_name='名称', max_length=64, unique=True)

    def __str__(self):
        return self.name


class FormerCode(models.Model):
    class Meta:
        verbose_name = '曾用课号'
        verbose_name_plural = verbose_name
        ordering = ['old_code']

    old_code = models.CharField(verbose_name='旧课号', max_length=32, unique=True)
    new_code = models.CharField(verbose_name='新课号', max_length=32)

    def __str__(self):
        return self.old_code


class Semester(models.Model):
    class Meta:
        verbose_name = '学期'
        verbose_name_plural = verbose_name
        ordering = ['-name']

    name = models.CharField(verbose_name='名称', max_length=64, unique=True)

    def __str__(self):
        return self.name


class Teacher(models.Model):
    class Meta:
        verbose_name = '教师'
        verbose_name_plural = verbose_name
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['tid', 'name'], name='unique_teacher')]

    tid = models.CharField(verbose_name='工号', max_length=32, null=True, blank=True, unique=True)
    name = models.CharField(verbose_name='姓名', max_length=255, db_index=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, verbose_name='单位', null=True, blank=True)
    title = models.CharField(verbose_name='职称', max_length=64, null=True, blank=True)
    pinyin = models.CharField(verbose_name='拼音', max_length=64, null=True, blank=True, db_index=True)
    abbr_pinyin = models.CharField(verbose_name='拼音缩写', max_length=64, null=True, blank=True, db_index=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    class Meta:
        verbose_name = '课程'
        verbose_name_plural = verbose_name
        ordering = ['code']
        constraints = [models.UniqueConstraint(fields=['code', 'main_teacher'], name='unique_course')]

    code = models.CharField(verbose_name='课号', max_length=32, db_index=True)
    name = models.CharField(verbose_name='名称', max_length=255, db_index=True)
    category = models.ForeignKey(Category, verbose_name='类别', null=True, blank=True, on_delete=models.SET_NULL)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, verbose_name='开课单位', null=True, blank=True)
    credit = models.FloatField(verbose_name='学分', default=0)
    main_teacher = models.ForeignKey(Teacher, verbose_name='主讲教师', on_delete=models.CASCADE, db_index=True)
    teacher_group = models.ManyToManyField(Teacher, verbose_name='教师组成', related_name='teacher_course')
    moderator_remark = models.TextField(verbose_name='管理员批注', null=True, blank=True, max_length=817)
    review_count = models.IntegerField(verbose_name='点评数', null=True, blank=True, default=0)
    review_avg = models.FloatField(verbose_name='平均评分', null=True, blank=True, default=0)

    def __str__(self):
        return f"{self.code} {self.name}（{self.main_teacher}）"


class Review(models.Model):
    class Meta:
        verbose_name = '点评'
        verbose_name_plural = verbose_name
        ordering = ['-created']
        constraints = [models.UniqueConstraint(fields=['user', 'course'], name='unique_review')]

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE, db_index=True)
    course = models.ForeignKey(Course, verbose_name='课程', on_delete=models.CASCADE, db_index=True)
    semester = models.ForeignKey(Semester, verbose_name='上课学期', on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField(verbose_name='推荐指数', validators=[MaxValueValidator(5), MinValueValidator(1)])
    comment = models.TextField(verbose_name='详细点评', max_length=817)
    created = models.DateTimeField(verbose_name='发布时间', default=timezone.now)
    score = models.CharField(verbose_name='成绩', null=True, blank=True, max_length=10)
    moderator_remark = models.TextField(verbose_name='管理员批注', null=True, blank=True, max_length=817)
    approve_count = models.IntegerField(verbose_name='获赞数', null=True, blank=True, default=0)
    disapprove_count = models.IntegerField(verbose_name='获踩数', null=True, blank=True, default=0)

    def __str__(self):
        return f"{self.user} 点评 {self.course}：{constrain_text(self.comment)}"

    def comment_validity(self):
        return constrain_text(self.comment)

    comment_validity.short_description = '详细点评'


class Notice(models.Model):
    class Meta:
        verbose_name = '通知'
        ordering = ['-created']
        verbose_name_plural = verbose_name

    title = models.CharField(verbose_name='标题', max_length=256)
    message = models.TextField(verbose_name='正文', max_length=256)
    created = models.DateTimeField(verbose_name='发布时间', default=timezone.now)
    available = models.BooleanField(verbose_name='是否显示', default=True)

    def __str__(self):
        return self.title


class Report(models.Model):
    class Meta:
        verbose_name = '反馈'
        ordering = ['-created']
        verbose_name_plural = verbose_name

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE, db_index=True)
    solved = models.BooleanField(verbose_name='是否解决', default=False)
    comment = models.TextField(verbose_name='反馈', max_length=817)
    created = models.DateTimeField(verbose_name='发布时间', default=timezone.now)
    reply = models.TextField(verbose_name='回复', max_length=817, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}：{constrain_text(self.comment)}"

    def comment_validity(self):
        return constrain_text(self.comment)

    def reply_validity(self):
        return constrain_text(self.reply)

    comment_validity.short_description = '反馈'
    reply_validity.short_description = '回复'


class Action(models.Model):
    ACTION_CHOICES = [(1, '赞同'), (-1, '反对'), (0, '重置')]

    class Meta:
        verbose_name = '评论点赞'
        verbose_name_plural = verbose_name
        constraints = [models.UniqueConstraint(fields=['user', 'review'], name='unique_action')]

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE)
    review = models.ForeignKey(Review, verbose_name='点评', on_delete=models.CASCADE, db_index=True)
    action = models.IntegerField(choices=ACTION_CHOICES, verbose_name='操作', default=0)

    def __str__(self):
        return f"{self.review}"


class ApiKey(models.Model):
    class Meta:
        verbose_name = 'Api密钥'
        verbose_name_plural = verbose_name

    key = models.CharField(max_length=255, unique=True)
    description = models.CharField(verbose_name='描述', max_length=255)
    is_enabled = models.BooleanField(verbose_name='启用', default=True)
    last_modified = models.DateTimeField(verbose_name='修改时间', default=timezone.now)

    def __str__(self):
        return f"{self.description}：{self.key} - {self.last_modified}"


class EnrollCourse(models.Model):
    class Meta:
        verbose_name = '选课记录'
        verbose_name_plural = verbose_name
        constraints = [models.UniqueConstraint(fields=['user', 'course', 'semester'], name='unique_enroll')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} {self.course.name} {self.semester.name}"
