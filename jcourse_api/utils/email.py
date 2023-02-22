from django.core.mail import send_mail

from jcourse import settings


def send_report_email(comment: str, time: str):
    email_body = f"内容：\n{comment}\n时间：{time}"
    send_mail('选课社区反馈', email_body, from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=[settings.ADMIN_EMAIL])
