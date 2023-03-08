from rest_framework.throttling import UserRateThrottle


class ReactionRateThrottle(UserRateThrottle):
    scope = 'review_reaction'


class VerifyAuthRateThrottle(UserRateThrottle):
    scope = 'verify_auth'


class EmailCodeRateThrottle(UserRateThrottle):
    scope = 'email_code'
