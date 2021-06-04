from django.urls import path

from oauth.views import login_jaccount, auth_jaccount, logout_auth

urlpatterns = [
    path('logout/', logout_auth, name='logout'),
    path('jaccount/login/', login_jaccount, name='login_jaccount'),
    path('jaccount/auth/', auth_jaccount, name='auth_jaccount')
]
