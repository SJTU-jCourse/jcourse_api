from django.contrib import admin

from ad.models import Touchpoint, Promotion


# Register your models here.
@admin.register(Touchpoint)
class TouchpointAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('touchpoint', 'available', 'description', 'created_at', 'click_times')
    readonly_fields = ('click_times', )
