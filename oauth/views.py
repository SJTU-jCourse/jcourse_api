import hashlib
import secrets
import smtplib

from authlib.integrations.base_client import OAuthError
from authlib.integrations.django_client import OAuth
from authlib.jose import jwt
from authlib.oidc.core import CodeIDToken
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.permissions import AllowAny

from jcourse import settings
from jcourse.settings import HASH_SALT, LOGIN_VERIFICATION_TIMEOUT
from jcourse.throttles import EmailCodeRateThrottle, VerifyEmailRateThrottle
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


def logout_auth(request):
    logout(request)
    return JsonResponse({'detail': 'logged out'})


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def login_auth(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'detail': '参数错误'}, status=400)

    login(request, user)
    return JsonResponse({'account': username})


def login_jaccount(request):
    redirect_uri = request.GET.get('redirect_uri', '')
    if redirect_uri == '':
        redirect_uri = request.build_absolute_uri(reverse('auth_jaccount'))
    return jaccount.authorize_redirect(request, redirect_uri)


def hash_username(username: str):
    return hashlib.blake2b((username + HASH_SALT).encode('ascii'), digest_size=16).hexdigest()


def auth_jaccount(request):
    try:
        token = jaccount.authorize_access_token(request)
    except OAuthError:
        return JsonResponse({'detail': '参数错误'}, status=400)
    claims = jwt.decode(token.get('id_token'),
                        jaccount.client_secret, claims_cls=CodeIDToken)
    user_type = claims['type']
    account = claims['sub']
    login_with(request, account, user_type)
    response = JsonResponse({'account': account})
    return response


def sync_lessons_login(request):
    redirect_uri = request.GET.get('redirect_uri', '')
    if redirect_uri == '':
        redirect_uri = request.build_absolute_uri(reverse('sync-lessons-auth'))
    return jaccount.authorize_redirect(request, redirect_uri, scope="basic lessons")


def sync_lessons_auth(request):
    try:
        token = jaccount.authorize_access_token(request)
    except OAuthError:
        return JsonResponse({'detail': '参数错误'}, status=400)
    request.session['token'] = token
    return JsonResponse({'detail': '同步状态就绪'})


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


@api_view(['POST'])
@throttle_classes([EmailCodeRateThrottle])
@permission_classes([AllowAny])
@csrf_exempt
def send_code(request):
    email: str = request.data.get("email", None)
    if email is None:
        return JsonResponse({'detail': '参数错误'}, status=400)
    email = email.strip().lower()
    if not email.endswith('@sjtu.edu.cn'):
        return JsonResponse({'detail': '请输入 SJTU 邮箱！'}, status=400)
    try:
        if send_code_email(email):
            return JsonResponse({'detail': '邮件已发送！请查看你的 SJTU 邮箱收件箱（包括垃圾邮件）。'})
    except smtplib.SMTPDataError:
        pass
    return JsonResponse({'detail': '验证码发送失败，请稍后重试。'}, status=500)


@api_view(['POST'])
@throttle_classes([VerifyEmailRateThrottle])
@permission_classes([AllowAny])
@csrf_exempt
def verify_and_login(request):
    email: str = request.data.get("email", None)
    code: str = request.data.get("code", None)
    if email is None or code is None:
        return JsonResponse({'detail': '参数错误'}, status=400)
    email = email.strip().lower()
    code = code.strip()
    if code != cache.get(email):
        return JsonResponse({'detail': '验证码错误，请重试。'}, status=400)
    account = email.split('@')[0]
    login_with(request, account, 'email')
    cache.delete(email)
    response = JsonResponse({'account': account})
    return response
