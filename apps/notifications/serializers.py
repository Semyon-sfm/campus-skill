from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    time_label = serializers.SerializerMethodField()
    workshop_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "title", "body", "is_read", "time_label", "workshop", "workshop_url"]

    def get_time_label(self, obj):
        created = timezone.localtime(obj.created_at)
        now = timezone.localtime()
        delta = now - created
        if delta.total_seconds() < 3600:
            minutes = max(1, int(delta.total_seconds() // 60))
            return f"{minutes} мин назад"
        if created.date() == now.date():
            return f"Сегодня · {created:%H:%M}"
        if (now.date() - created.date()).days == 1:
            return f"Вчера · {created:%H:%M}"
        return f"{created:%d.%m} · {created:%H:%M}"

    def get_workshop_url(self, obj):
        if not obj.workshop_id:
            return None
        return reverse("workshops:detail", args=[obj.workshop_id])
