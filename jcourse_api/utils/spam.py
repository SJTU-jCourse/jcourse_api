import datetime
import difflib

from django.contrib.auth.models import User

from jcourse_api.models import Review
from jcourse_api.utils import send_antispam_email

SPAM_MAX_REVIEWS = 3
SPAM_PERIOD_MINUTES = 5
SPAM_SIMILAR_RATIO = 0.75


def check_spam(user: User, data, time: datetime.datetime):
    # find review history
    time_threshold = time - datetime.timedelta(minutes=SPAM_PERIOD_MINUTES)
    reviews = Review.objects.filter(user=user, created_at__gt=time_threshold).order_by("-created_at")[:SPAM_MAX_REVIEWS]

    if reviews.count() + 1 < SPAM_MAX_REVIEWS:
        return False

    comment = data["comment"]
    count = 0

    # compare with former reviews
    s = difflib.SequenceMatcher(lambda x: x in " \t\n\r:,.：，。")
    s.set_seq1(comment)
    for review in reviews:
        s.set_seq2(review.comment)
        if s.quick_ratio() > SPAM_SIMILAR_RATIO:
            count = count + 1
    if count * 2 >= SPAM_MAX_REVIEWS:
        return True
    return False


def deal_with_spam(user: User):
    user.is_active = False
    user.save(update_fields=["is_active"])
    send_antispam_email(user.username)
