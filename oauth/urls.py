from django.urls import path

from oauth.views import *

urlpatterns = [
    path('logout/', auth_logout, name='logout'),
    path('login/', auth_login, name='login'),
    path('email/send-code/', auth_email_send_code, name='send_code'),
    path('email/verify/', auth_email_verify, name='verify_email'),
    path('jaccount/login/', login_jaccount, name='login_jaccount'),
    path('jaccount/auth/', auth_jaccount, name='auth_jaccount'),
    path('sync-lessons/login/', sync_lessons_login, name='sync-lessons-login'),
    path('sync-lessons/auth/', sync_lessons_auth, name='sync-lessons-auth'),
]
