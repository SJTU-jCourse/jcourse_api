import hashlib
import re
from random import Random

from authlib.integrations.base_client import OAuthError
from authlib.integrations.django_client import OAuth
from authlib.jose import jwt
from authlib.oidc.core import CodeIDToken
from django.contrib.auth import login, logout
from django.contrib.auth.models import User

from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.urls import reverse
from rest_framework.views import APIView

from jcourse import settings
from jcourse.settings import HASH_SALT
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


def login_with(request, account: str, user_type: str):
    lower = account.lower()
    former_username = hash_username(account)
    username = hash_username(lower)
    try:
        user = User.objects.get(username=former_username)
        user.username = username
        user.save()
    except User.DoesNotExist:
        user, _ = User.objects.get_or_create(username=username)
    UserProfile.objects.update_or_create(user=user, defaults={'user_type': user_type, 'lowercase': True})
    login(request, user)


def logout_auth(request):
    logout(request)
    return JsonResponse({'details': 'logged out'})


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
        return JsonResponse({'details': 'Bad argument!'}, status=400)
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
        return JsonResponse({'details': 'Bad argument!'}, status=400)
    request.session['token'] = token
    return JsonResponse({'details': 'Sync Status Ready!'})


# 生成随机字符串
def random_str(random_length=8):
    rand_str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(random_length):
        rand_str += chars[random.randint(0, length)]
    return rand_str


def send_code_email(email):
    code = random_str(16)
    email_title = "选课社区登录"
    email_body = "您的登录验证码为：{0}，10分钟内有效，请尽快进行验证。".format(code)
    send_status = send_mail(email_title, email_body, settings.DEFAULT_FROM_EMAIL, [email])
    if not send_status:
        return False
    return code


# 注册发送邮箱验证码
class LoginWithEmailView(APIView):

    def post(self, request):
        email = request.POST.get("email", None)
        code = request.POST.get("code", None)
        # 发送验证码
        if code is None:
            sjtu_email = re.search('.*@sjtu.edu.cn$', email)
            if sjtu_email is None:
                response = JsonResponse({'status': 'error', 'message': '请输入交大邮箱！'}, status=400)
                return response
            else:
                code = send_code_email(email)
                if code:
                    cache.set(email, code)
                    response = JsonResponse({'status': 'success', 'message': '邮件已发送！'})
                    return response
                else:
                    response = JsonResponse({'status': 'error', 'message': '验证码发送失败，请稍后重试。'}, status=400)
                    return response
        # 验证码验证
        else:
            if code == cache.get(email):
                account = email.split('@')
                hashed_username = hash_username(account[0])
                login_with(request, hashed_username, 'email')
                response = JsonResponse({'status': 'success', 'message': '用户' + account[0] + '登陆成功！'})
                return response
            else:
                response = JsonResponse({'status': 'error', 'message': '验证码错误，请重试。'}, status=400)
                return response
