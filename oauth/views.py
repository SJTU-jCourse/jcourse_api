import hashlib

from authlib.integrations.base_client import OAuthError
from authlib.integrations.django_client import OAuth
from authlib.jose import jwt
from authlib.oidc.core import CodeIDToken
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse

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


def login_with(request, username: str, user_type: str):
    with transaction.atomic():
        user, _ = User.objects.get_or_create(username=username)
        UserProfile.objects.update_or_create(user=user, defaults={'user_type': user_type})
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
    hashed_username = hash_username(account)
    login_with(request, hashed_username, user_type)
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
