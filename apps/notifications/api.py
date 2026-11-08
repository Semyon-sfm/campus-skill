from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(
    mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "workshop"
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "unread": queryset.filter(is_read=False).count(),
                "results": serializer.data,
            }
        )

    @action(detail=False, methods=["post"])
    def read(self, request):
        """Отмечает всё прочитанным — вызывается при открытии страницы уведомлений."""
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"marked": updated, "unread": 0})
