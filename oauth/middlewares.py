from django.http import HttpRequest

from oauth.tasks import update_last_seen_at


class LastSeenAtMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request: HttpRequest):
        if request.user.is_authenticated:
            update_last_seen_at(request.user)
        response = self.get_response(request)
        return response
