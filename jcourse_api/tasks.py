from celery import shared_task
from django.core.mail import send_mail

from jcourse import settings


@shared_task
def email_report_to_admin(data):
    email_body = f"内容：\n{data['comment']}\n时间：{data['created']}"
    send_mail('选课社区反馈', email_body, from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=[settings.ADMIN_EMAIL])
