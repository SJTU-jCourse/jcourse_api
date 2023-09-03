from django.contrib.auth.models import User
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, task

from oauth.models import UserProfile
from utils.common import get_time_now


@db_periodic_task(crontab(day='*/1'))
def release_banned_users():
    now = get_time_now()
    should_release_users = UserProfile.objects.filter(suspended_till__isnull=False,
                                                      suspended_till__lt=now)
    User.objects.filter(userprofile__in=should_release_users).update(is_active=True)
    should_release_users.update(suspended_till=None)


@task()
def update_last_seen_at(user: User):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.last_seen_at = get_time_now()
    profile.save()
