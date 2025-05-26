from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, Avg, Q
from django.utils import timezone

from jcourse_api.models import constrain_text, Course, Semester
from utils.cut_word import get_cut_word_search_vector


class Review(models.Model):
    class Meta:
        verbose_name = '点评'
        verbose_name_plural = verbose_name
        ordering = ['-modified_at']
        constraints = [models.UniqueConstraint(fields=['user', 'course'], name='unique_review')]
        indexes = [GinIndex(fields=['search_vector'])]

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE, db_index=True)
    course = models.ForeignKey(Course, verbose_name='课程', on_delete=models.CASCADE, db_index=True)
    semester = models.ForeignKey(Semester, verbose_name='上课学期', on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField(verbose_name='推荐指数', validators=[MaxValueValidator(5), MinValueValidator(1)])
    comment = models.TextField(verbose_name='详细点评', max_length=9681)
    created_at = models.DateTimeField(verbose_name='发布时间', default=timezone.now, db_index=True)
    modified_at = models.DateTimeField(verbose_name='修改时间', blank=True, null=True, db_index=True)
    score = models.CharField(verbose_name='成绩', null=True, blank=True, max_length=10)
    moderator_remark = models.TextField(verbose_name='管理员批注', null=True, blank=True, max_length=817)
    approve_count = models.IntegerField(verbose_name='获赞数', null=True, blank=True, default=0, db_index=True)
    disapprove_count = models.IntegerField(verbose_name='获踩数', null=True, blank=True, default=0, db_index=True)
    search_vector = SearchVectorField(null=True, editable=False)

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
            if previous.comment != self.comment:
                self.search_vector = get_cut_word_search_vector(self.comment)
        super().save(force_insert, force_update, using, update_fields)
        if need_to_update:
            update_course_reviews(self.course)
            if old_course and old_course != self.course:
                update_course_reviews(old_course)


class ReviewRevision(models.Model):
    class Meta:
        verbose_name = '点评修订记录'
        verbose_name_plural = verbose_name

    review = models.ForeignKey(Review, verbose_name='点评', on_delete=models.SET_NULL, db_index=True, null=True)
    user = models.ForeignKey(User, verbose_name='执行用户', on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey(Course, verbose_name='课程', on_delete=models.SET_NULL, null=True)
    semester = models.ForeignKey(Semester, verbose_name='上课学期', on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField(verbose_name='推荐指数', validators=[MaxValueValidator(5), MinValueValidator(1)])
    comment = models.TextField(verbose_name='详细点评', max_length=9681)
    created_at = models.DateTimeField(verbose_name='修订时间', default=timezone.now, db_index=True)
    score = models.CharField(verbose_name='成绩', null=True, blank=True, max_length=10)

    def comment_validity(self):
        return constrain_text(self.comment)

    comment_validity.short_description = '详细点评'


class ReviewReaction(models.Model):
    class ReactionType(models.IntegerChoices):
        RESET = 0, '重置'
        APPROVE = 1, '赞同'
        DISAPPROVE = -1, '反对'

    class Meta:
        verbose_name = '点评回应'
        verbose_name_plural = verbose_name
        ordering = ['-modified_at']
        constraints = [models.UniqueConstraint(fields=['user', 'review'], name='unique_reaction')]

    user = models.ForeignKey(User, verbose_name='用户', on_delete=models.CASCADE, db_index=True)
    review = models.ForeignKey(Review, verbose_name='点评', on_delete=models.CASCADE, db_index=True)
    reaction = models.IntegerField(choices=ReactionType.choices, verbose_name='操作', default=0, db_index=True)
    modified_at = models.DateTimeField(verbose_name='修改时间', blank=True, null=True, db_index=True, auto_now=True)

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


def update_review_reactions(review: Review):
    actions = ReviewReaction.objects.filter(review=review).aggregate(approves=Count('reaction', filter=Q(reaction=1)),
                                                                     disapproves=Count('reaction',
                                                                                       filter=Q(reaction=-1)))
    review.approve_count = actions['approves']
    review.disapprove_count = actions['disapproves']
    review.save(update_fields=['approve_count', 'disapprove_count'])


def update_course_reviews(course: Course):
    review = Review.objects.filter(course=course).aggregate(avg=Avg('rating'), count=Count('*'))
    course.review_count = review['count']
    course.review_avg = review['avg']
    course.save(update_fields=['review_count', 'review_avg'])
