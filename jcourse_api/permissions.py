from jcourse import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission


class CustomBasePermission(BasePermission):

    def has_permission(self, request, view):
        if settings.BENCHMARK:
            return True
        return bool(request.user and request.user.is_authenticated)


class IsOwnerOrAdminOrReadOnly(CustomBasePermission):
    message = '您只能修改自己发表的内容。'

    def has_object_permission(self, request, view, obj):
        if self.has_permission(request, view):
            if request.method in SAFE_METHODS:
                return True
            return obj.user == request.user or request.user.is_staff
        else:
            return False


class IsAdminOrReadOnly(CustomBasePermission):
    message = '当前仅管理员可以发表和修改内容。'

    def has_permission(self, request, view):
        if request.user:
            if request.method in SAFE_METHODS:
                return True
            return request.user.is_staff
        else:
            return False
