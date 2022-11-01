from rest_framework.throttling import UserRateThrottle


class ReactionRateThrottle(UserRateThrottle):
    scope = 'review_reaction'


class VerifyEmailRateThrottle(UserRateThrottle):
    scope = 'verify_email'


class EmailCodeRateThrottle(UserRateThrottle):
    scope = 'email_code'
