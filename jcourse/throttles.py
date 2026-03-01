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
            ip_addr = self.get_ident(request)
            ident = f"{ip_addr}"
        return f'throttle_{self.scope}_{ident}'


class ReactionRateThrottle(SuperUserExemptRateThrottle):
    scope = 'review_reaction'

    def get_cache_key(self, request, view):
        # 对于reaction，必须基于用户ID进行限流
        if request.user.is_authenticated:
            # 使用用户ID作为限流标识符
            ident = f"user_{request.user.pk}"
        else:
            # 未认证用户不允许点赞
            ip_addr = self.get_ident(request)
            ident = f"anonymous_{ip_addr}"
        return f'throttle_{self.scope}_{ident}'


class VerifyAuthRateThrottle(SuperUserExemptRateThrottle):
    scope = 'verify_auth'

    def get_cache_key(self, request, view):
        # 对于验证码验证，需要基于邮箱地址进行限流
        account = request.data.get('account') or request.data.get('username')
        if account:
            # 使用邮箱地址作为限流标识符
            ident = f"email_{account.strip().lower()}"
        elif request.user.is_authenticated:
            # 如果没有提供account但用户已认证，使用用户ID
            ident = f"user_{request.user.pk}"
        else:
            # 如果都没有，使用IP地址
            ip_addr = self.get_ident(request)
            ident = f"ip_{ip_addr}"
        return f'throttle_{self.scope}_{ident}'


class EmailCodeRateThrottle(SuperUserExemptRateThrottle):
    scope = 'email_code'

    def get_cache_key(self, request, view):
        # 对于验证码发送，需要基于邮箱地址进行限流
        account = request.data.get('account')
        if account:
            # 使用邮箱地址作为限流标识符
            ident = f"email_{account.strip().lower()}"
        elif request.user.is_authenticated:
            # 如果没有提供account但用户已认证，使用用户ID
            ident = f"user_{request.user.pk}"
        else:
            # 如果都没有，使用IP地址作为后备
            ip_addr = self.get_ident(request)
            ident = f"ip_{ip_addr}"
        return f'throttle_{self.scope}_{ident}'
