import hashlib
import secrets

from authlib.integrations.django_client import OAuth
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import send_mail

from jcourse import settings
from jcourse.settings import HASH_SALT, LOGIN_VERIFICATION_TIMEOUT
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


def send_code_email(email: str):
    code = secrets.token_hex(3)
    email_title = "选课社区验证码"
    email_body = f"您好！\n\n" \
                 f"请使用以下验证码完成登录，{LOGIN_VERIFICATION_TIMEOUT}分钟内有效：\n\n" \
                 f"{code}\n\n" \
                 f"如非本人操作请忽略该邮件。\n\n" \
                 f"选课社区"
    cache.set(email, code, LOGIN_VERIFICATION_TIMEOUT * 60)
    return send_mail(email_title, email_body, settings.DEFAULT_FROM_EMAIL, [email])


def get_or_create_user(account: str):
    lower = account.lower()
    former_username = hash_username(account)
    username = hash_username(lower)

    user = User.objects.filter(username=former_username)
    if not user.exists():
        user, _ = User.objects.get_or_create(username=username)
        return user

    user = User.objects.filter(username=username)
    if user.exists():
        return user.first()

    user = User.objects.get(username=former_username)
    user.username = username
    user.save()
    return user


def login_with(request, account: str, user_type: str):
    user = get_or_create_user(account)
    UserProfile.objects.update_or_create(user=user, defaults={'user_type': user_type, 'lowercase': True})
    login(request, user)