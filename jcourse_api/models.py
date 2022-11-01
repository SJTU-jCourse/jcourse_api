from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, Avg, Q
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

    def count(self):
        return Course.objects.filter(department=self).count()

    count.short_description = '课程数量'


class Category(models.Model):
    class Meta:
        verbose_name = '课程类别'
        ordering = ['name']
        verbose_name_plural = verbose_name

    name = models.CharField(verbose_name='名称', max_length=64, unique=True)

    def __str__(self):
        return self.name

    def count(self):
        return Course.objects.filter(categories=self).count()

    count.short_description = '课程数量'


class FormerCode(models.Model):
    class Meta:
        verbose_name = '曾用课号'
        verbose_name_plural = verbose_name
        ordering = ['old_code']

    old_code = models.CharField(verbose_name='旧课号', max_length=32, unique=True, db_index=True)
    new_code = models.CharField(verbose_name='新课号', max_length=32, db_index=True)

    def __str__(self):
        return self.old_code


class Semester(models.Model):
    class Meta:
        verbose_name = '学期'
        verbose_name_plural = verbose_name
        ordering = ['-name']

    name = models.CharField(verbose_name='名称', max_length=64, unique=True)
    available = models.BooleanField(verbose_name='用户可选', default=True)

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
    # 仅用于后台维护，不对外显示
    last_semester = models.ForeignKey(Semester, verbose_name='最后更新学期', null=True, blank=True,
                                      on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        (0, '管理员回复'),
        (1, '获得点赞'),
        (2, '积分失效'),
        (3, '积分补偿'),
        (4, '点评被回复'),
        (5, '点评被引用'),
        (6, '点评被删除'),
        (7, '反馈被回复'),
        (8, '关注的课程有新点评'),

    )

    NOTIFICATION_TYPE = {
        'admin_reply': 0,
        'get_likes': 1,
        'points_invalid': 2,
        'points_compensate': 3,
        'reviews_replied': 4,
        'reviews_quoted': 5,
        'reviews_removed': 6,
        'reports_replied': 7,
        'courses_new_review': 8,
    }

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = verbose_name
        # abstract = True
        ordering = ('-created',)
        index_together = ('recipient',)

    actor = models.ForeignKey(
        User,
        blank=False,
        related_name='notify_actor',
        on_delete=models.CASCADE,
        verbose_name='发送者',
    )
    recipient = models.ForeignKey(
        User,
        blank=False,
        related_name='notify_recipient',
        on_delete=models.CASCADE,
        verbose_name='接收者',
    )

    type = models.IntegerField(verbose_name='类型', default=0, choices=NOTIFICATION_TYPE_CHOICES, )

    @admin.display(description='类型')
    def type_word(self):
        return self.NOTIFICATION_TYPE_CHOICES[self.type][1]

    description = models.TextField(blank=True, null=True, verbose_name='内容')

    content_type = models.ForeignKey(ContentType, models.CASCADE, verbose_name='内容类型', null=True)
    object_id = models.PositiveIntegerField(verbose_name='内容ID', null=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    created = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='创建时间')
    read_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name='阅读时间')

    @admin.display(description='已读', boolean=True)
    def read(self):
        return self.read_at is not None

    public = models.BooleanField(default=True, db_index=True, verbose_name='已发布')
    emailed = models.BooleanField(default=False, db_index=True, verbose_name='已发送邮件')

    def __str__(self):
        return f"{self.id}"


class Course(models.Model):
    class Meta:
        verbose_name = '课程'
        verbose_name_plural = verbose_name
        ordering = ['code']
        constraints = [models.UniqueConstraint(fields=['code', 'main_teacher'], name='unique_course')]

    code = models.CharField(verbose_name='课号', max_length=32, db_index=True)
    name = models.CharField(verbose_name='名称', max_length=255, db_index=True)
    categories = models.ManyToManyField(Category, verbose_name='类别', db_index=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, verbose_name='开课单位',
                                   null=True, blank=True, db_index=True)
    credit = models.FloatField(verbose_name='学分', default=0)
    main_teacher = models.ForeignKey(Teacher, verbose_name='主讲教师', on_delete=models.CASCADE, db_index=True)
    teacher_group = models.ManyToManyField(Teacher, verbose_name='教师组成', related_name='teacher_course')
    moderator_remark = models.TextField(verbose_name='管理员批注', null=True, blank=True, max_length=817)
    review_count = models.IntegerField(verbose_name='点评数', null=True, blank=True, default=0, db_index=True)
    review_avg = models.FloatField(verbose_name='平均评分', null=True, blank=True, default=0, db_index=True)
    # 仅用于后台维护，不对外显示
    last_semester = models.ForeignKey(Semester, verbose_name='最后更新学期', null=True, blank=True,
                                      on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.code} {self.name}（{self.main_teacher}）"

    def category_names(self):
        return ','.join(self.categories.all().values_list('name', flat=True))

    category_names.short_description = '类别'


class Review(models.Model):
    class Meta:
        verbose_name = '点评'
        verbose_name_plural = verbose_name
        ordering = ['-modified']
        constraints = [models.UniqueConstraint(fields=['user', 'course'], name='unique_review')]

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE, db_index=True)
    course = models.ForeignKey(Course, verbose_name='课程', on_delete=models.CASCADE, db_index=True)
    semester = models.ForeignKey(Semester, verbose_name='上课学期', on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField(verbose_name='推荐指数', validators=[MaxValueValidator(5), MinValueValidator(1)])
    comment = models.TextField(verbose_name='详细点评', max_length=9681)
    created = models.DateTimeField(verbose_name='发布时间', default=timezone.now, db_index=True)
    modified = models.DateTimeField(verbose_name='修改时间', blank=True, null=True, db_index=True)
    score = models.CharField(verbose_name='成绩', null=True, blank=True, max_length=10)
    moderator_remark = models.TextField(verbose_name='管理员批注', null=True, blank=True, max_length=817)
    approve_count = models.IntegerField(verbose_name='获赞数', null=True, blank=True, default=0, db_index=True)
    disapprove_count = models.IntegerField(verbose_name='获踩数', null=True, blank=True, default=0, db_index=True)

    def __str__(self):
        return f"{self.user} 点评 {self.course}：{constrain_text(self.comment)}"

    def comment_validity(self):
        return constrain_text(self.comment)

    comment_validity.short_description = '详细点评'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        need_to_update = False
        old_course = None
        if self.pk is None:
            need_to_update = True
        else:
            previous = Review.objects.get(pk=self.pk)
            if previous.course_id != self.course_id or previous.rating != self.rating:
                need_to_update = True
                old_course = previous.course
        super().save(force_insert, force_update, using, update_fields)
        if need_to_update:
            update_course_reviews(self.course)
            if old_course and old_course != self.course:
                update_course_reviews(old_course)


class ReviewRevision(models.Model):
    class Meta:
        verbose_name = '点评修订记录'
        verbose_name_plural = verbose_name

    review = models.ForeignKey(Review, verbose_name='点评', on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(User, verbose_name='执行用户', on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey(Course, verbose_name='课程', on_delete=models.SET_NULL, null=True)
    semester = models.ForeignKey(Semester, verbose_name='上课学期', on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField(verbose_name='推荐指数', validators=[MaxValueValidator(5), MinValueValidator(1)])
    comment = models.TextField(verbose_name='详细点评', max_length=9681)
    created = models.DateTimeField(verbose_name='修订时间', default=timezone.now, db_index=True)
    score = models.CharField(verbose_name='成绩', null=True, blank=True, max_length=10)

    def comment_validity(self):
        return constrain_text(self.comment)

    comment_validity.short_description = '详细点评'


class Announcement(models.Model):
    class Meta:
        verbose_name = '公告'
        ordering = ['-created']
        verbose_name_plural = verbose_name

    title = models.CharField(verbose_name='标题', max_length=256)
    message = models.TextField(verbose_name='正文', max_length=256)
    url = models.TextField(verbose_name='链接', max_length=256, null=True, blank=True)
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
    solved = models.BooleanField(verbose_name='是否解决', default=False, db_index=True)
    comment = models.TextField(verbose_name='反馈', max_length=817)
    created = models.DateTimeField(verbose_name='发布时间', default=timezone.now, db_index=True)
    reply = models.TextField(verbose_name='回复', max_length=817, null=True, blank=True)
    notification = GenericRelation(Notification)

    def __str__(self):
        return f"{self.user}：{constrain_text(self.comment)}"

    def comment_validity(self):
        return constrain_text(self.comment)

    def reply_validity(self):
        return constrain_text(self.reply)

    comment_validity.short_description = '反馈'
    reply_validity.short_description = '回复'


class ReviewReaction(models.Model):
    REACTION_CHOICES = [(1, '赞同'), (-1, '反对'), (0, '重置')]

    class Meta:
        verbose_name = '点评回应'
        verbose_name_plural = verbose_name
        ordering = ['-modified']
        constraints = [models.UniqueConstraint(fields=['user', 'review'], name='unique_reaction')]

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE, db_index=True)
    review = models.ForeignKey(Review, verbose_name='点评', on_delete=models.CASCADE, db_index=True)
    reaction = models.IntegerField(choices=REACTION_CHOICES, verbose_name='操作', default=0, db_index=True)
    modified = models.DateTimeField(verbose_name='修改时间', blank=True, null=True, db_index=True, auto_now=True)

    def __str__(self):
        return f"{self.user} {self.get_reaction_display()} {self.review.id}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        need_to_update = False
        old_review = None
        if self.pk is None:
            need_to_update = True
        else:
            previous = ReviewReaction.objects.get(pk=self.pk)
            if previous.review_id != self.review_id or previous.reaction != self.reaction:
                need_to_update = True
                old_review = previous.review
        super().save(force_insert, force_update, using, update_fields)
        if need_to_update:
            update_review_reactions(self.review)
            if old_review and old_review != self.review:
                update_review_reactions(old_review)


class ApiKey(models.Model):
    class Meta:
        verbose_name = 'Api密钥'
        verbose_name_plural = verbose_name

    key = models.CharField(max_length=255, unique=True, db_index=True)
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

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE, db_index=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_index=True)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)

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


def update_review_reactions(review: Review):
    actions = ReviewReaction.objects.filter(review=review).aggregate(approves=Count('reaction', filter=Q(reaction=1)),
                                                                     disapproves=Count('reaction', filter=Q(reaction=-1)))
    review.approve_count = actions['approves']
    review.disapprove_count = actions['disapproves']
    review.save(update_fields=['approve_count', 'disapprove_count'])


def update_course_reviews(course: Course):
    review = Review.objects.filter(course=course).aggregate(avg=Avg('rating'), count=Count('*'))
    course.review_count = review['count']
    course.review_avg = review['avg']
    course.save(update_fields=['review_count', 'review_avg'])


def send_report_replied_notification(report: Report):
    if report.reply:
        notification = Notification.objects.create(
            actor=report.user,  # maybe need a system account to send this notification
            recipient=report.user,
            type=Notification.NOTIFICATION_TYPE['reports_replied'],
            content_type=ContentType.objects.get_for_model(report),
            object_id=report.id,
            created=timezone.now()
        )
        notification.save()
