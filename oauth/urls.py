from django.urls import path

from oauth.views import *

urlpatterns = [
    path('logout/', auth_logout, name='logout'),
    path('login/', auth_login, name='login'),
    path('email/send-code/', auth_email_send_code, name='email_send_code'),
    path('email/verify/', auth_email_verify_code, name='email_verify_code'),
    path('email/login/', auth_email_verify_password, name='email_verify_password'),
    path('reset-password/send-code/', reset_password_send_code, name='reset_password_send'),
    path('reset-password/reset/', reset_password_reset, name='reset_password_reset'),
    path('jaccount/login/', login_jaccount, name='login_jaccount'),
    path('jaccount/auth/', auth_jaccount, name='auth_jaccount'),
    path('sync-lessons/login/', sync_lessons_login, name='sync-lessons-login'),
    path('sync-lessons/auth/', sync_lessons_auth, name='sync-lessons-auth'),
]
