from django.contrib import admin
from django.db import IntegrityError
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from jcourse_api.models import Course, Teacher, FormerCode, Department, Semester, Review, Category, Language, Report, \
    Action, Notice


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
        exclude = ('id',)
        export_order = (
            'code', 'name', 'credit', 'department', 'category', 'language', 'main_teacher', 'teacher_group')

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        try:
            super().save_instance(instance, using_transactions, dry_run)
        except IntegrityError:
            pass


class CourseAdmin(ImportExportModelAdmin):
    list_display = ('id', 'code', 'name', 'credit', 'department', 'category', 'main_teacher')
    list_filter = ('department', 'category')
    search_fields = ('id', 'code', 'name')
    autocomplete_fields = ('main_teacher', 'teacher_group')
    resource_class = CourseResource


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


class TeacherAdmin(ImportExportModelAdmin):
    resource_class = TeacherResource
    list_display = ('tid', 'name', 'department', 'title', 'pinyin', 'abbr_pinyin')
    list_filter = ('department__name',)
    inlines = [CourseInline]
    search_fields = ('name', 'pinyin', 'abbr_pinyin')


class FormerCodeAdmin(ImportExportModelAdmin):
    list_display = ('old_code', 'new_code')


class ReviewAdmin(ImportExportModelAdmin):
    list_display = ('user', 'course', 'comment_validity', 'created', 'approves', 'disapproves')
    search_fields = ('user', 'course')

    def approves(self, obj):
        return Action.objects.filter(review=obj, action=1).count()

    def disapproves(self, obj):
        return Action.objects.filter(review=obj, action=-1).count()

    approves.short_description = '赞同数'
    disapproves.short_description = '反对数'


class ReportAdmin(ImportExportModelAdmin):
    list_display = ('user', 'solved', 'comment_validity', 'created')


class ApproveAdmin(ImportExportModelAdmin):
    list_display = ('user', 'review', 'action')


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


class DepartmentAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name')
    resource_class = DepartmentResource


class NameAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name')


admin.site.register(Department, DepartmentAdmin)
admin.site.register(Semester, NameAdmin)
admin.site.register(Category, NameAdmin)
admin.site.register(Language, NameAdmin)
admin.site.register(Action, ApproveAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(FormerCode, FormerCodeAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Notice, NoticeAdmin)
