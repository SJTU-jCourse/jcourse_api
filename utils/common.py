from datetime import datetime

from django.utils.timezone import get_current_timezone


def get_time_now():
    return datetime.now(tz=get_current_timezone())
