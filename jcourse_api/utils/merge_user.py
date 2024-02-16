from django.db import transaction

from jcourse_api.models import *
from oauth.models import *
from oauth.utils import hash_username


def merge_user(old_user: User, new_user: User) -> bool:
    with transaction.atomic():
        Review.objects.filter(user=old_user).update(user=new_user)
        ReviewReaction.objects.filter(user=old_user).update(user=new_user)
        Report.objects.filter(user=old_user).update(user=new_user)
        EnrollCourse.objects.filter(user=old_user).update(user=new_user)
        UserPoint.objects.filter(user=old_user).update(user=new_user)
        Notification.objects.filter(recipient=old_user).update(recipient=new_user)
        CourseNotificationLevel.objects.filter(user=old_user).update(user=new_user)
        UserProfile.objects.filter(user=old_user).update(user=new_user)
        old_user.delete()
    return True


def merge_user_by_id(old_id: int, new_id: int) -> bool:
    if old_id == new_id:
        return False
    try:
        old_user = User.objects.get(pk=old_id)
        new_user = User.objects.get(pk=new_id)
        return merge_user(old_user, new_user)
    except Course.DoesNotExist:
        return False


def merge_user_by_raw_account(old_account: str, new_account: str) -> bool:
    if old_account == new_account:
        return False
    try:
        old_name = hash_username(old_account)
        new_name = hash_username(new_account)
        old_user = User.objects.get(username=old_name)
        new_user = User.objects.get(username=new_name)
        return merge_user(old_user, new_user)
    except Course.DoesNotExist:
        return False
