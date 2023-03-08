from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from jcourse_api.models import *
from jcourse_api.serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user, public=True).order_by('-created_at')

    @action(detail=True, methods=['POST'])
    def read(self, request: Request, pk=None):
        if 'read' not in request.data:
            return Response({'error': '未指定操作类型！'}, status=status.HTTP_400_BAD_REQUEST)
        notification: Notification = self.get_object()
        if notification.recipient != request.user:
            return Response({'error': '无权操作！'}, status=status.HTTP_403_FORBIDDEN)
        if int(request.data['read']):
            notification.read_at = timezone.now()
        else:
            notification.read_at = None
        notification.save()

        return Response({'id': pk,
                         'read_at': notification.read_at},
                        status=status.HTTP_200_OK)
