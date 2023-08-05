from django.core.mail import send_mail

from jcourse import settings


def send_admin_email(title: str, body: str):
    try:
        send_mail(title, body, from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[settings.ADMIN_EMAIL])
    except:
        pass
