from authlib.integrations.django_client import OAuth
from authlib.jose import jwt
from authlib.oidc.core import CodeIDToken
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
# Create your views here.
from django.urls import reverse

from jcourse import settings

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


def auth_jaccount(request):
    client = oauth.jaccount
    token = client.authorize_access_token(request)
    claims = jwt.decode(token.get('id_token'),
                        client.client_secret, claims_cls=CodeIDToken)
    login_with(request, claims['sub'])
    return redirect('/')
