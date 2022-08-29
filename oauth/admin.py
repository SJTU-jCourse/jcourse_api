from django.contrib import admin

# Register your models here.
from oauth.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'lowercase')
    search_fields = ('user__username',)
    list_filter = ('user_type', 'lowercase')
    readonly_fields = ('user', 'user_type', 'lowercase')
