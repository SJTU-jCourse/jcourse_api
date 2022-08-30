from rest_framework.throttling import UserRateThrottle


class ActionRateThrottle(UserRateThrottle):
    scope = 'review_action'


class VerifyEmailRateThrottle(UserRateThrottle):
    scope = 'verify_email'


class EmailCodeRateThrottle(UserRateThrottle):
    scope = 'email_code'
