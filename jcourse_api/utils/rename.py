from django.contrib.auth.models import User

from oauth.utils import hash_username


def rename_user(user: User, new_name: str):
    user.username = new_name
    user.save(update_fields=["username"])


def rename_user_by_name(old_name: str, new_name: str) -> bool:
    try:
        user = User.objects.get(username=old_name)
        rename_user(user, new_name)
    except User.DoesNotExist:
        return False
    return True


def rename_user_raw_account(old_account: str, new_account: str):
    old_name = hash_username(old_account)
    new_name = hash_username(new_account)
    return rename_user_by_name(old_name, new_name)
