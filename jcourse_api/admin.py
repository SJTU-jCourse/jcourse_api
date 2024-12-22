import os

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

    def save_instance(self, instance, is_create, row, **kwargs):
        try:
            super().save_instance(instance, is_create, row, **kwargs)
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

    def save_instance(self, instance, is_create, row, **kwargs):
        try:
            super().save_instance(instance, is_create, row, **kwargs)
        except IntegrityError:
            pass


@admin.register(Teacher)
class TeacherAdmin(ImportExportModelAdmin):
    resource_class = TeacherResource
    list_display = ('id', 'tid', 'name', 'department', 'title', 'pinyin', 'abbr_pinyin', 'last_semester')
    list_filter = ('department', 'title', 'last_semester')
    search_fields = ('name', 'pinyin', 'abbr_pinyin')


class FormerCodeResource(resources.ModelResource):
    class Meta:
        model = FormerCode
        import_id_fields = ('old_code', 'new_code')
        skip_unchanged = True
        report_skipped = False
        exclude = ('id',)
        export_order = ('old_code', 'new_code')
        use_bulk = True

    def save_instance(self, instance, is_create, row, **kwargs):
        try:
            super().save_instance(instance, is_create, row, **kwargs)
        except IntegrityError:
            pass


@admin.register(FormerCode)
class FormerCodeAdmin(ImportExportModelAdmin):
    resource_class = FormerCodeResource
    list_display = ('old_code', 'new_code')
    search_fields = ('old_code', 'new_code')


@admin.register(Review)
class ReviewAdmin(ImportExportModelAdmin):
    autocomplete_fields = ('user', 'course')
    list_display = (
        'id', 'user', 'course', 'created_at', 'modified_at', 'approve_count', 'disapprove_count', 'comment_validity')
    search_fields = ('user__username', 'course__code', 'course__id')
    readonly_fields = ('approve_count', 'disapprove_count')


@admin.register(ReviewRevision)
class ReviewRevisionAdmin(ImportExportModelAdmin):
    autocomplete_fields = ('user', 'review', 'course')
    list_display = ('id', 'review_id', 'user', 'course', 'created_at', 'comment_validity')
    search_fields = ('review__id', 'user__username', 'course__code', 'course__id')


@admin.register(Report)
class ReportAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user', 'solved', 'reply_validity', 'comment_validity', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('solved',)
    readonly_fields = ('user', 'comment', 'created_at')


@admin.register(ReviewReaction)
class ReactionAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user', 'reaction', 'modified_at', 'review')
    search_fields = ('user__username', 'review__course__code', 'review__id')
    readonly_fields = ('user', 'review',)


@admin.register(Announcement)
class AnnouncementAdmin(ImportExportModelAdmin):
    list_display = ('id', 'title', 'message', 'created_at', 'url', 'available')


class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        exclude = ('id', 'count')
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('name',)

    def save_instance(self, instance, is_create, row, **kwargs):
        try:
            super().save_instance(instance, is_create, row, **kwargs)
        except IntegrityError:
            pass


class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        exclude = ('id', 'count')
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('name',)

    def save_instance(self,instance, is_create, row, **kwargs):
        try:
            super().save_instance(instance, is_create, row, **kwargs)
        except IntegrityError:
            pass


@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'count')
    search_fields = ('name',)
    resource_class = DepartmentResource

    def count(self, obj):
        return Course.objects.filter(department=obj).count()

    count.short_description = '课程数量'


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'count')
    search_fields = ('name',)
    resource_class = CategoryResource

    def count(self, obj):
        return Course.objects.filter(categories=obj).count()

    count.short_description = '课程数量'


@admin.register(Semester)
class SemesterAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'available')


@admin.register(UserPoint)
class UserPointAdmin(ImportExportModelAdmin):
    autocomplete_fields = ('user',)
    list_display = ('id', 'user', 'value', 'description', 'time')
    search_fields = ('user__username', 'description')


@admin.register(EnrollCourse)
class EnrollCourseAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user', 'course', 'semester', 'created_at')
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
    autocomplete_fields = ('recipient',)
    list_display = ('id', 'type', 'recipient', 'read', 'public')
    list_filter = ('public', 'created_at', 'read_at', 'type')
    actions = ['mark_as_read', 'mark_as_unread']

    @admin.action(description='设为已读')
    def mark_as_read(self, request, queryset):
        queryset.update(read_at=timezone.now())

    @admin.action(description='设为未读')
    def mark_as_unread(self, request, queryset):
        queryset.update(read_at=None)


@admin.register(CourseNotificationLevel)
class CourseNotificationLevelAdmin(ImportExportModelAdmin):
    list_display = ('id', 'course', 'user', 'notification_level', 'modified_at')
    list_filter = ('notification_level',)
    search_fields = ('course__code', 'user__username')
    search_help_text = '输入课程代码或用户名'
