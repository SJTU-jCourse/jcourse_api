from django.contrib.auth.models import User
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from oauth.models import UserProfile
from utils.common import get_time_now


@db_periodic_task(crontab(day='*'))
def release_banned_users():
    now = get_time_now()
    should_release_users = UserProfile.objects.filter(suspended_till__isnull=False,
                                                      suspended_till__lt=now)
    User.objects.filter(userprofile__in=should_release_users).update(is_active=True)
    should_release_users.update(suspended_till=None)
