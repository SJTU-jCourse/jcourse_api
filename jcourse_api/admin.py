import os

from django.contrib import admin
from django.db import IntegrityError
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from jcourse_api.models import *


class CourseResource(resources.ModelResource):
    department = fields.Field(attribute='department', widget=ForeignKeyWidget(Department, 'name'))
    categories = fields.Field(attribute='categories', widget=ManyToManyWidget(Category, separator=';', field='name'))
    main_teacher = fields.Field(attribute='main_teacher', widget=ForeignKeyWidget(Teacher, 'tid'))
    teacher_group = fields.Field(attribute='teacher_group',
                                 widget=ManyToManyWidget(Teacher, separator=';', field='tid'))
    last_semester = fields.Field(attribute='last_semester', widget=ForeignKeyWidget(Semester, 'name'))

    class Meta:
        model = Course
        import_id_fields = ('code', 'main_teacher')
        exclude = ('id', 'review_count', 'review_avg')
        skip_unchanged = True
        report_skipped = False
        export_order = (
            'code', 'name', 'credit', 'department', 'categories', 'main_teacher', 'teacher_group', 'last_semester')

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        try:
            super().save_instance(instance, using_transactions, dry_run)
        except IntegrityError:
            pass


@admin.register(Course)
class CourseAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'code', 'name', 'credit', 'department', 'category_names', 'main_teacher', 'review_count', 'review_avg',
        'last_semester')
    list_filter = ('department', 'categories', 'credit', 'last_semester')
    search_fields = ('id', 'code', 'name')
    autocomplete_fields = ('main_teacher', 'teacher_group', 'department', 'categories')
    resource_class = CourseResource
    readonly_fields = ('review_count', 'review_avg')


class TeacherResource(resources.ModelResource):
    department = fields.Field(attribute='department', widget=ForeignKeyWidget(Department, 'name'))
    last_semester = fields.Field(attribute='last_semester', widget=ForeignKeyWidget(Semester, 'name'))

    class Meta:
        model = Teacher
        import_id_fields = ('tid',)
        skip_unchanged = True
        report_skipped = False
        exclude = ('id',)
        export_order = ('tid', 'name', 'department', 'title', 'last_semester')

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        try:
            super().save_instance(instance, using_transactions, dry_run)
        except IntegrityError:
            pass


@admin.register(Teacher)
class TeacherAdmin(ImportExportModelAdmin):
    resource_class = TeacherResource
    list_display = ('tid', 'name', 'department', 'title', 'pinyin', 'abbr_pinyin', 'last_semester')
    list_filter = ('department', 'title', 'last_semester')
    search_fields = ('name', 'pinyin', 'abbr_pinyin')


@admin.register(FormerCode)
class FormerCodeAdmin(ImportExportModelAdmin):
    list_display = ('old_code', 'new_code')
    search_fields = ('old_code', 'new_code')


@admin.register(Review)
class ReviewAdmin(ImportExportModelAdmin):
    autocomplete_fields = ('user', 'course')
    list_display = (
        'user', 'course', 'created', 'modified', 'approve_count', 'disapprove_count', 'comment_validity')
    search_fields = ('user__username', 'course__code', 'course__id')
    readonly_fields = ('approve_count', 'disapprove_count')


@admin.register(Report)
class ReportAdmin(ImportExportModelAdmin):
    list_display = ('user', 'solved', 'reply_validity', 'comment_validity', 'created')
    search_fields = ('user__username',)
    list_filter = ('solved',)
    readonly_fields = ('user', 'comment', 'created')


@admin.register(Action)
class ActionAdmin(ImportExportModelAdmin):
    list_display = ('user', 'action', 'review',)
    search_fields = ('user__username', 'review__course__code')
    readonly_fields = ('user', 'review',)


@admin.register(Notice)
class NoticeAdmin(ImportExportModelAdmin):
    list_display = ('title', 'message', 'created', 'url', 'available')


class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        exclude = ('id', 'count')
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('name',)

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        try:
            super().save_instance(instance, using_transactions, dry_run)
        except IntegrityError:
            pass


class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        exclude = ('id', 'count')
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('name',)

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        try:
            super().save_instance(instance, using_transactions, dry_run)
        except IntegrityError:
            pass


@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'count')
    search_fields = ('name',)
    resource_class = DepartmentResource


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'count')
    search_fields = ('name',)
    resource_class = CategoryResource


@admin.register(Semester)
class SemesterAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'available')


@admin.register(UserPoint)
class UserPointAdmin(ImportExportModelAdmin):
    autocomplete_fields = ('user',)
    list_display = ('user', 'value', 'description', 'time')
    search_fields = ('user__username', 'description')


@admin.register(EnrollCourse)
class EnrollCourseAdmin(ImportExportModelAdmin):
    list_display = ('user', 'course', 'semester')
    search_fields = ('user__username', 'course__code')
    readonly_fields = ('user', 'course', 'semester')


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'key':
            field.initial = os.urandom(16).hex()
        return field


@admin.register(Notification)
class NotificationAdmin(ImportExportModelAdmin):
    # raw_id_fields = ('recipient',)
    list_display = ('type_word', 'recipient', 'actor', 'read', 'public', 'emailed')

    list_filter = ('read', 'public', 'create_at', 'read_at', 'type')
    actions = ['mark_as_read',
               'mark_as_unread',
               'mark_as_emailed_and_email',
               'mark_as_emailed_but_not_email',
               'mark_as_not_emailed',
               ]

    def get_queryset(self, request):
        qs = super(NotificationAdmin, self).get_queryset(request)
        return qs.prefetch_related('actor')

    @admin.action(description='设为已读')
    def mark_as_read(self, request, queryset):
        queryset.update(read=True, readAt=timezone.now())

    @admin.action(description='设为未读')
    def mark_as_unread(self, request, queryset):
        queryset.update(read=False, readAt=None)

    @admin.action(description='标记为已发送邮件-并发送邮件')
    def mark_as_emailed_and_email(self, request, queryset):
        queryset.update(emailed=True)
        for notification in queryset:
            # 邮件发送部分
            pass

    @admin.action(description='标记为已发送邮件-但不发送邮件')
    def mark_as_emailed_but_not_email(self, request, queryset):
        queryset.update(emailed=True)

    @admin.action(description='标记为未发送邮件')
    def mark_as_not_emailed(self, request, queryset):
        queryset.update(emailed=False)
