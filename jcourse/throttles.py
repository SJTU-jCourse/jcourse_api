from rest_framework.request import Request
from rest_framework.throttling import UserRateThrottle


class SuperUserExemptRateThrottle(UserRateThrottle):

    def allow_request(self, request: Request, view):
        if request.user.is_superuser:
            return True
        return super().allow_request(request, view)


class ReactionRateThrottle(SuperUserExemptRateThrottle):
    scope = 'review_reaction'


class VerifyAuthRateThrottle(SuperUserExemptRateThrottle):
    scope = 'verify_auth'


class EmailCodeRateThrottle(SuperUserExemptRateThrottle):
    scope = 'email_code'
