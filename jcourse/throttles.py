from rest_framework.request import Request
from rest_framework.throttling import UserRateThrottle


class SuperUserExemptRateThrottle(UserRateThrottle):

    def allow_request(self, request: Request, view):
        if request.user.is_superuser:
            return True
        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = f"user_{request.user.pk}"
        else:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_addr = self.get_ident(request)
            ident = f"{ip_addr}_{user_agent}"
        return f'throttle_{self.scope}_{ident}'


class ReactionRateThrottle(SuperUserExemptRateThrottle):
    scope = 'review_reaction'


class VerifyAuthRateThrottle(SuperUserExemptRateThrottle):
    scope = 'verify_auth'


class EmailCodeRateThrottle(SuperUserExemptRateThrottle):
    scope = 'email_code'
