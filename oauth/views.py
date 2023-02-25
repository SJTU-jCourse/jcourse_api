import smtplib

from authlib.integrations.base_client import OAuthError
from authlib.jose import jwt
from authlib.oidc.core import CodeIDToken
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.permissions import AllowAny

from jcourse.throttles import EmailCodeRateThrottle, VerifyEmailRateThrottle
from oauth.utils import send_code_email, login_with, jaccount, generate_code, store_email_code, verify_email_code, \
    clean_email_code, verify_email_times


def auth_logout(request):
    logout(request)
    return JsonResponse({'detail': 'logged out'})


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def auth_login(request):
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


@api_view(['POST'])
@throttle_classes([EmailCodeRateThrottle])
@permission_classes([AllowAny])
@csrf_exempt
def auth_email_send_code(request):
    email: str = request.data.get("email", None)
    if email is None:
        return JsonResponse({'detail': '参数错误'}, status=400)
    email = email.strip().lower()
    if not email.endswith('@sjtu.edu.cn'):
        return JsonResponse({'detail': '请输入 SJTU 邮箱！'}, status=400)
    try:
        code = generate_code()
        store_email_code(email, code)
        if send_code_email(email, code):
            return JsonResponse({'detail': '邮件已发送！请查看你的 SJTU 邮箱收件箱（包括垃圾邮件）。'})
    except smtplib.SMTPDataError:
        pass
    return JsonResponse({'detail': '验证码发送失败，请稍后重试。'}, status=500)


@api_view(['POST'])
@throttle_classes([VerifyEmailRateThrottle])
@permission_classes([AllowAny])
@csrf_exempt
def auth_email_verify(request):
    email: str = request.data.get("email", None)
    code: str = request.data.get("code", None)
    if email is None or code is None:
        return JsonResponse({'detail': '参数错误'}, status=400)
    email = email.strip().lower()
    code = code.strip()
    if not verify_email_times(email):
        return JsonResponse({'detail': '尝试次数达到上限，请稍后重试。'}, status=429)
    if not verify_email_code(email, code):
        return JsonResponse({'detail': '验证码错误，请重试。'}, status=400)
    account = email.split('@')[0]
    login_with(request, account)
    clean_email_code(email)
    response = JsonResponse({'account': account})
    return response
