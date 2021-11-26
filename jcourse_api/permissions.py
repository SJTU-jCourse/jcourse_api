from rest_framework.permissions import SAFE_METHODS, IsAuthenticated


class IsOwnerOrReadOnly(IsAuthenticated):
    message = 'You must be the owner to modify.'

    def has_object_permission(self, request, view, obj):
        if self.has_permission(request, view):
            if request.method in SAFE_METHODS:
                return True
            return obj.user == request.user
        else:
            return False
