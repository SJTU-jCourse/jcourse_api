import hashlib
import secrets
import string

from authlib.integrations.django_client import OAuth
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.cache import cache

import utils.mail
from jcourse import settings
from jcourse.settings import HASH_SALT, EMAIL_VERIFICATION_TIMEOUT, EMAIL_VERIFICATION_MAX_TIMES
from oauth.models import UserProfile

oauth = OAuth()
oauth.register(
    name='jaccount',
    client_id=settings.AUTHLIB_OAUTH_CLIENTS['jaccount']['client_id'],
    client_secret=settings.AUTHLIB_OAUTH_CLIENTS['jaccount']['client_secret'],
    access_token_url='https://jaccount.sjtu.edu.cn/oauth2/token',
    authorize_url='https://jaccount.sjtu.edu.cn/oauth2/authorize',
    api_base_url='https://api.sjtu.edu.cn/',
    client_kwargs={"scope": "basic"}
)
jaccount = oauth.jaccount


def hash_username(username: str):
    return hashlib.blake2b((username + HASH_SALT).encode('ascii'), digest_size=16).hexdigest()


def generate_code(length: int = 6):
    code = ''.join(secrets.choice(string.digits) for _ in range(length))
    return code


def build_email_auth_cache_key(account: str):
    return f"email_auth_code_{account}"


def build_email_auth_times_cache_key(account: str):
    return f"email_auth_times_{account}"


def auth_store_email_code(account: str, code: str):
    cache.set(build_email_auth_cache_key(account), code, EMAIL_VERIFICATION_TIMEOUT * 60)


def auth_get_email_code(account: str):
    return cache.get(build_email_auth_cache_key(account))


def auth_get_email_tries(account: str):
    return cache.get(build_email_auth_times_cache_key(account))


def auth_verify_times(account: str):
    times_key = build_email_auth_times_cache_key(account)
    times = cache.get_or_set(times_key, 0, EMAIL_VERIFICATION_TIMEOUT * 60)
    cache.incr(times_key)
    return times < EMAIL_VERIFICATION_MAX_TIMES


def auth_verify_email_code(account: str, code: str):
    account = account.strip().lower()
    code = code.strip()
    return code == cache.get(build_email_auth_cache_key(account))


def clean_email_code(account: str):
    cache.delete_many([build_email_auth_cache_key(account), build_email_auth_times_cache_key(account)])


def send_code_email(email: str, code: str):
    email_title = "选课社区验证码"
    email_body = f"您好！\n\n" \
                 f"请使用以下验证码完成登录，{EMAIL_VERIFICATION_TIMEOUT}分钟内有效：\n\n" \
                 f"{code}\n\n" \
                 f"如非本人操作请忽略该邮件。\n\n" \
                 f"选课社区"
    return send_mail(email_title, email_body, email)


def get_or_create_user(account: str):
    lower = account.lower()
    former_username = hash_username(account)
    username = hash_username(lower)

    # 查找旧号存在情况
    user = User.objects.filter(username=former_username)
    if not user.exists():  # 如果旧号不存在，建新号
        user, _ = User.objects.get_or_create(username=username)
        return user
    # 如果旧号存在，查找新号存在情况
    user = User.objects.filter(username=username)
    if user.exists():  # 如果新号存在，直接返回新号（未合并旧号，可以管理员操作）
        return user.first()
    # 如果新号不存在，把修改旧号用户名为新用户名
    user = User.objects.get(username=former_username)
    user.username = username
    user.save()
    return user


def login_with(request, account: str, user_type: str | None = None):
    user = get_or_create_user(account)
    if user_type:
        UserProfile.objects.update_or_create(user=user, defaults={'user_type': user_type, 'lowercase': True})
    else:
        UserProfile.objects.update_or_create(user=user, defaults={'lowercase': True})
    login(request, user)


def build_email_reset_cache_key(account: str):
    return f"email_reset_code_{account}"


def reset_store_email_code(account: str, code: str):
    cache.set(build_email_reset_cache_key(account), code, EMAIL_VERIFICATION_TIMEOUT * 60)


def reset_send_code_email(email: str, code: str):
    email_title = "选课社区验证码"
    email_body = f"您好！\n\n" \
                 f"请使用以下验证码完成密码重置，{EMAIL_VERIFICATION_TIMEOUT}分钟内有效：\n\n" \
                 f"{code}\n\n" \
                 f"如非本人操作请忽略该邮件。\n\n" \
                 f"选课社区"
    return send_mail(email_title, email_body, email)

def send_mail(title, body, recipient):
    if settings.TESTING or settings.BENCHMARK:
        return True

    sender = settings.EMAIL_HOST_USER
    pwd = settings.EMAIL_HOST_PASSWORD
    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT
    use_ssl = settings.EMAIL_USE_SSL
    try:
        utils.mail.send_mail_inner(sender, sender, pwd, [recipient], title, body, host, port, use_ssl)
    except Exception as e:
        return False
    return True


def reset_verify_email_code(account: str, code: str):
    account = account.strip().lower()
    code = code.strip()
    return code == cache.get(build_email_reset_cache_key(account))


def reset_get_email_code(account: str):
    return cache.get(build_email_reset_cache_key(account))


def reset_clean_email_code(account: str):
    cache.delete_many([build_email_reset_cache_key(account)])


def get_user_profile(user: User):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile
