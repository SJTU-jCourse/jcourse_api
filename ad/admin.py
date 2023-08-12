from django.contrib import admin

from ad.models import Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('touchpoint', 'available', 'description', 'created_at', 'click_times')
    readonly_fields = ('click_times',)
