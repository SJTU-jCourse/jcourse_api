from django.urls import path

from oauth.views import *

urlpatterns = [
    path('logout/', logout_auth, name='logout'),
    path('email/send-code/', send_code, name='send_code'),
    path('email/verify/', verify_and_login, name='verify_email'),
    path('jaccount/login/', login_jaccount, name='login_jaccount'),
    path('jaccount/auth/', auth_jaccount, name='auth_jaccount'),
    path('sync-lessons/login/', sync_lessons_login, name='sync-lessons-login'),
    path('sync-lessons/auth/', sync_lessons_auth, name='sync-lessons-auth'),
]
