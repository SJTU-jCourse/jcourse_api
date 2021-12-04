import os

from django.contrib import admin
from django.db import IntegrityError
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from jcourse_api.models import *


class CourseInline(admin.StackedInline):
    model = Course
    extra = 1


class CourseResource(resources.ModelResource):
    department = fields.Field(attribute='department', widget=ForeignKeyWidget(Department, 'name'))
    category = fields.Field(attribute='category', widget=ForeignKeyWidget(Category, 'name'))
    language = fields.Field(attribute='language', widget=ForeignKeyWidget(Language, 'name'))
    main_teacher = fields.Field(attribute='main_teacher', widget=ForeignKeyWidget(Teacher, 'tid'))
    teacher_group = fields.Field(attribute='teacher_group',
                                 widget=ManyToManyWidget(Teacher, separator=';', field='tid'))

    class Meta:
        model = Course
        import_id_fields = ('code', 'main_teacher')
        exclude = ('id', 'review_count', 'review_avg')
        export_order = (
            'code', 'name', 'credit', 'department', 'category', 'language', 'main_teacher', 'teacher_group')

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        try:
            super().save_instance(instance, using_transactions, dry_run)
        except IntegrityError:
            pass


@admin.register(Course)
class CourseAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'code', 'name', 'credit', 'department', 'category', 'main_teacher', 'review_count', 'review_avg')
    list_filter = ('department', 'category')
    search_fields = ('id', 'code', 'name')
    autocomplete_fields = ('main_teacher', 'teacher_group')
    resource_class = CourseResource
    readonly_fields = ('review_count', 'review_avg')


class TeacherResource(resources.ModelResource):
    department = fields.Field(attribute='department', widget=ForeignKeyWidget(Department, 'name'))

    class Meta:
        model = Teacher
        import_id_fields = ('tid',)
        exclude = ('id',)
        export_order = ('tid', 'name', 'department', 'title')

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        try:
            super().save_instance(instance, using_transactions, dry_run)
        except IntegrityError:
            pass


@admin.register(Teacher)
class TeacherAdmin(ImportExportModelAdmin):
    resource_class = TeacherResource
    list_display = ('tid', 'name', 'department', 'title', 'pinyin', 'abbr_pinyin')
    list_filter = ('department__name',)
    inlines = [CourseInline]
    search_fields = ('name', 'pinyin', 'abbr_pinyin')


@admin.register(FormerCode)
class FormerCodeAdmin(ImportExportModelAdmin):
    list_display = ('old_code', 'new_code')
    search_fields = ('old_code', 'new_code')


@admin.register(Review)
class ReviewAdmin(ImportExportModelAdmin):
    list_display = ('user', 'course', 'created', 'approve_count', 'disapprove_count', 'comment_validity')
    search_fields = ('user__username', 'course__code')
    readonly_fields = ('approve_count', 'disapprove_count')


@admin.register(Report)
class ReportAdmin(ImportExportModelAdmin):
    list_display = ('user', 'solved', 'reply_validity', 'comment_validity', 'created')
    search_fields = ('user__username',)
    list_filter = ('solved',)


@admin.register(Action)
class ActionAdmin(ImportExportModelAdmin):
    list_display = ('user', 'action', 'review',)
    search_fields = ('user__username', 'review__course__code')


@admin.register(Notice)
class NoticeAdmin(ImportExportModelAdmin):
    list_display = ('available', 'title', 'message', 'created')


class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        exclude = ('id',)
        import_id_fields = ('name',)

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        try:
            super().save_instance(instance, using_transactions, dry_run)
        except IntegrityError:
            pass


@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name')
    resource_class = DepartmentResource


@admin.register(Semester, Category, Language)
class NameAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name')


@admin.register(EnrollCourse)
class EnrollCourseAdmin(ImportExportModelAdmin):
    list_display = ('user', 'course', 'semester')
    search_fields = ('user__username', 'course__code')


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'key':
            field.initial = os.urandom(16).hex()
        return field
