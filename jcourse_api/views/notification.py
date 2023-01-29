from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from jcourse_api.models import *
from jcourse_api.serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user, public=True).order_by('-created')

    @action(detail=True, methods=['POST'])
    def read(self, request: Request, pk=None):
        if 'read' not in request.data:
            return Response({'error': '未指定操作类型！'}, status=status.HTTP_400_BAD_REQUEST)
        # if pk is None:
        #     return Response({'error': '未指定通知id！'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            notification = Notification.objects.get(id=pk, recipient=request.user)
            if int(request.data['read']):
                notification.read_at = timezone.now()
            else:
                notification.read_at = None
            notification.save()
        except Notification.DoesNotExist:
            return Response({'error': '无指定通知！'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'id': pk,
                         'read_at': notification.read_at},
                        status=status.HTTP_200_OK)
