from django.core.mail import send_mail

from jcourse import settings


def send_admin_email(title: str, body: str):
    try:
        send_mail(title, body, from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[settings.ADMIN_EMAIL])
    except:
        pass


def send_report_email(comment: str, time: str):
    send_admin_email('选课社区反馈', f"内容：\n{comment}\n时间：{time}")


def send_antispam_email(username: str):
    send_admin_email('选课社区风控', f"用户：\n{username} 由于刷点评，已被自动封号")
