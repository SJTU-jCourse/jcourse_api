import datetime
import difflib

from django.contrib.auth.models import User
from django.db.models import QuerySet

import utils.common
from jcourse_api.models import Review, Course
from jcourse_api.tasks import send_antispam_email
from oauth.utils import get_user_profile

SPAM_MAX_REVIEWS = 3
SPAM_PERIOD_MINUTES = 5
SPAM_SIMILAR_RATIO = 0.85


def similar_rule(data: dict, reviews: QuerySet):
    comment = data["comment"]
    count = 0
    s = difflib.SequenceMatcher(lambda x: x in " \t\n\r:,.：，。")
    s.set_seq1(comment)
    for review in reviews:
        s.set_seq2(review.comment)
        if s.quick_ratio() > SPAM_SIMILAR_RATIO:
            count = count + 1
    return count * 2 >= SPAM_MAX_REVIEWS


def course_rule(data: dict, reviews: QuerySet):
    count = 0
    try:
        course = Course.objects.get(pk=data["course"])
    except Course.DoesNotExist:
        return False
    for review in reviews:
        if review.course.code == course.code:
            count = count + 1
    return count == SPAM_MAX_REVIEWS


def check_spam(user: User, data, time: datetime.datetime):
    # find review history
    time_threshold = time - datetime.timedelta(minutes=SPAM_PERIOD_MINUTES)
    reviews = Review.objects.select_related("course").filter(user=user, created_at__gt=time_threshold).order_by(
        "-created_at")[:SPAM_MAX_REVIEWS]

    if reviews.count() + 1 < SPAM_MAX_REVIEWS:
        return False
    if course_rule(data, reviews):
        return True
    if similar_rule(data, reviews):
        return True

    return False


def deal_with_spam(user: User, data: dict):
    suspended_till = utils.common.get_time_now() + datetime.timedelta(days=SPAM_MAX_REVIEWS * 30)
    userprofile = get_user_profile(user)
    userprofile.suspended_till = suspended_till
    userprofile.save(update_fields=['suspended_till'])
    send_antispam_email(user.username, data)
