from rest_framework.permissions import SAFE_METHODS, IsAuthenticated


class IsOwnerOrReadOnly(IsAuthenticated):
    message = '您只能修改自己发表的内容。'

    def has_object_permission(self, request, view, obj):
        if self.has_permission(request, view):
            if request.method in SAFE_METHODS:
                return True
            return obj.user == request.user
        else:
            return False


class IsAdminOrReadOnly(IsAuthenticated):
    message = '当前仅管理员可以发表和修改内容。'

    def has_permission(self, request, view):
        if request.user:
            if request.method in SAFE_METHODS:
                return True
            return request.user.is_staff
        else:
            return False
