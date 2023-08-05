from huey.contrib.djhuey import task

from jcourse_api.utils import send_admin_email


@task()
def send_report_email(comment: str, time: str):
    send_admin_email('选课社区反馈', f"内容：\n{comment}\n时间：{time}")


@task()
def send_antispam_email(username: str, data: dict):
    send_admin_email('选课社区风控', f"用户：{username} 由于刷点评，已被自动封号。最近点评为：\n{data}")
