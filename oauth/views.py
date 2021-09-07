import hashlib
from datetime import timedelta

from authlib.integrations.django_client import OAuth
from authlib.jose import jwt
from authlib.oidc.core import CodeIDToken
from django.conf.global_settings import SESSION_COOKIE_AGE
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
# Create your views here.
from django.urls import reverse
from django.utils.datetime_safe import datetime

from jcourse import settings
from jcourse.settings import HASH_SALT, SESSION_COOKIE_SECURE

oauth = OAuth()
oauth.register(
    name='jaccount',
    client_id=settings.AUTHLIB_OAUTH_CLIENTS['jaccount']['client_id'],
    client_secret=settings.AUTHLIB_OAUTH_CLIENTS['jaccount']['client_secret'],
    access_token_url='https://jaccount.sjtu.edu.cn/oauth2/token',
    authorize_url='https://jaccount.sjtu.edu.cn/oauth2/authorize',
    api_base_url='https://api.sjtu.edu.cn/',
    client_kwargs={
        "scope": "openid",
        "token_endpoint_auth_method": "client_secret_basic",
        "token_placement": "header"
    }
)
jaccount = oauth.jaccount


def login_with(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(username=username)
    login(request, user)


def logout_auth(request):
    logout(request)
    return redirect('/login')


def login_jaccount(request):
    redirect_uri = request.build_absolute_uri(reverse('auth_jaccount'))
    return oauth.jaccount.authorize_redirect(request, redirect_uri)


def hash_username(username):
    return hashlib.blake2b((username + HASH_SALT).encode('ascii'), digest_size=16).hexdigest()


def auth_jaccount(request):
    token = jaccount.authorize_access_token(request)
    claims = jwt.decode(token.get('id_token'),
                        jaccount.client_secret, claims_cls=CodeIDToken)
    account = claims['sub']
    hashed_username = hash_username(account)
    login_with(request, hashed_username)
    response = redirect('/')
    expires = datetime.strftime(datetime.utcnow() + timedelta(seconds=SESSION_COOKIE_AGE), "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie('account', account, expires=expires,
                        samesite='lax',
                        secure=SESSION_COOKIE_SECURE)
    return response


def sync_lessons_login(request):
    redirect_uri = request.build_absolute_uri(reverse('sync-lessons-auth'))
    return oauth.jaccount.authorize_redirect(request, redirect_uri, scope="openid lessons")


def sync_lessons_auth(request):
    token = jaccount.authorize_access_token(request)
    request.session['token'] = token
    response = redirect(f'/sync')
    return response
