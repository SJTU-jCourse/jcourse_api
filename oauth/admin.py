from django.contrib import admin

# Register your models here.
from oauth.models import UserProfile
from oauth.utils import hash_username


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'lowercase', 'last_seen_at', 'suspended_till')
    search_fields = ('user__username',)
    list_filter = ('user_type', 'lowercase', 'last_seen_at', 'suspended_till')
    readonly_fields = ('user', 'user_type', 'lowercase')
    actions = ["reactive_user"]

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        hashed = hash_username(search_term)
        queryset |= self.model.objects.filter(user__username=hashed)
        return queryset, may_have_duplicates

    @admin.action(description="解封用户")
    def reactive_user(self, request, queryset):
        for userprofile in queryset:
            userprofile.suspended_till = None
            userprofile.save(update_fields=["suspended_till"])
