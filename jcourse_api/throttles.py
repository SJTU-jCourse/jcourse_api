from rest_framework.throttling import UserRateThrottle


class ActionRateThrottle(UserRateThrottle):
    scope = 'review_action'
