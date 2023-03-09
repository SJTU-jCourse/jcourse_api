import smtplib

from authlib.integrations.base_client import OAuthError
from authlib.jose import jwt
from authlib.oidc.core import CodeIDToken
from django.contrib.auth import logout, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.permissions import AllowAny

from jcourse.throttles import EmailCodeRateThrottle, VerifyAuthRateThrottle
from oauth.utils import *


def auth_logout(request):
    logout(request)
    return JsonResponse({'detail': '已登出。'})


@api_view(['POST'])
@throttle_classes([VerifyAuthRateThrottle])
@permission_classes([AllowAny])
@csrf_exempt
def auth_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if username is None or password is None:
        return JsonResponse({'detail': '参数错误。'}, status=400)
    if not auth_verify_times(username):
        return JsonResponse({'detail': '尝试次数达到上限，请稍后重试。'}, status=429)
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'detail': '用户名或密码错误。'}, status=400)
    login(request, user)
    clean_email_code(username)
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
        return JsonResponse({'detail': '参数错误。'}, status=400)
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
        return JsonResponse({'detail': '参数错误。'}, status=400)
    request.session['token'] = token
    return JsonResponse({'detail': '同步状态就绪。'})


@api_view(['POST'])
@throttle_classes([EmailCodeRateThrottle])
@permission_classes([AllowAny])
@csrf_exempt
def auth_email_send_code(request):
    account: str = request.data.get("account", None)
    if account is None:
        return JsonResponse({'detail': '参数错误。'}, status=400)
    account = account.strip().lower()
    try:
        code = generate_code()
        auth_store_email_code(account, code)
        if send_code_email(account + "@sjtu.edu.cn", code):
            return JsonResponse({'detail': '邮件已发送！请查看你的 SJTU 邮箱收件箱（包括垃圾邮件）。'})
    except smtplib.SMTPDataError:
        pass
    return JsonResponse({'detail': '验证码发送失败，请稍后重试。'}, status=500)


@api_view(['POST'])
@throttle_classes([VerifyAuthRateThrottle])
@permission_classes([AllowAny])
@csrf_exempt
def auth_email_verify_code(request):
    account: str = request.data.get("account", None)
    code: str = request.data.get("code", None)
    if account is None or code is None:
        return JsonResponse({'detail': '参数错误。'}, status=400)
    account = account.strip().lower()
    code = code.strip()
    if not auth_verify_times(account):
        return JsonResponse({'detail': '尝试次数达到上限，请稍后重试。'}, status=429)
    if not auth_verify_email_code(account, code):
        return JsonResponse({'detail': '验证码错误，请重试。'}, status=400)
    login_with(request, account)
    clean_email_code(account)
    response = JsonResponse({'account': account})
    return response


@api_view(['POST'])
@throttle_classes([VerifyAuthRateThrottle])
@permission_classes([AllowAny])
@csrf_exempt
def auth_email_verify_password(request):
    account = request.data.get('account')
    password = request.data.get('password')

    if account is None or password is None:
        return JsonResponse({'detail': '参数错误。'}, status=400)
    account = account.strip().lower()
    password = password.strip()
    username = hash_username(account)

    if not auth_verify_times(account):
        return JsonResponse({'detail': '尝试次数达到上限，请稍后重试。'}, status=429)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'detail': '邮箱或者密码错误。'}, status=400)

    login(request, user)
    clean_email_code(account)
    return JsonResponse({'account': account})


@api_view(['POST'])
@throttle_classes([EmailCodeRateThrottle])
def reset_password_send_code(request):
    account: str = request.data.get("account", None)
    if account is None:
        return JsonResponse({'detail': '参数错误。'}, status=400)
    account = account.strip().lower()
    if request.user.username != hash_username(account):
        return JsonResponse({'detail': '请输入本账号对应的邮箱！'}, status=400)
    try:
        code = generate_code()
        reset_store_email_code(account, code)
        if reset_send_code_email(account + "@sjtu.edu.cn", code):
            return JsonResponse({'detail': '邮件已发送！请查看你的 SJTU 邮箱收件箱（包括垃圾邮件）。'})
    except smtplib.SMTPDataError:
        pass
    return JsonResponse({'detail': '验证码发送失败，请稍后重试。'}, status=500)


@api_view(['POST'])
@throttle_classes([VerifyAuthRateThrottle])
def reset_password_reset(request):
    account: str = request.data.get("account", None)
    code: str = request.data.get("code", None)
    password: str = request.data.get("password", None)
    if account is None or code is None or password is None:
        return JsonResponse({'detail': '参数错误。'}, status=400)
    account = account.strip().lower()
    if request.user.username != hash_username(account):
        return JsonResponse({'detail': '请输入本账号对应的邮箱！'}, status=400)
    if not reset_verify_email_code(account, code):
        return JsonResponse({'detail': '验证码错误，请重试。'}, status=400)
    try:
        validate_password(password, request.user)
    except ValidationError:
        return JsonResponse({'detail': "密码太弱！请至少9位长度，包含字母和数字，并且不是常见密码。"}, status=400)
    reset_clean_email_code(account)
    request.user.set_password(password)
    request.user.save()
    return JsonResponse({"detail": "更改密码成功。"})
