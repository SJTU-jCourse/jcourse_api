from django.contrib import admin

# Register your models here.
from oauth.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type')
    search_fields = ('user__username',)
    list_filter = ('user_type',)
    readonly_fields = ('user', 'user_type')
