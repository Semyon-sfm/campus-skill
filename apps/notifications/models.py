from django.conf import settings
from django.db import models


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="получатель",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField("заголовок", max_length=160)
    body = models.CharField("текст", max_length=300)
    workshop = models.ForeignKey(
        "workshops.Workshop",
        verbose_name="воркшоп",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField("прочитано", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "уведомление"
        verbose_name_plural = "уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.full_name}: {self.title}"


class NotificationSettings(models.Model):
    REMINDER_CHOICES = [(24, "За сутки"), (2, "За 2 часа"), (1, "За 1 час")]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="пользователь",
        on_delete=models.CASCADE,
        related_name="notification_settings",
    )
    status_changes = models.BooleanField("изменения статуса записи", default=True)
    reminders = models.BooleanField("напоминания о встречах", default=True)
    reminder_hours = models.PositiveSmallIntegerField(
        "когда напомнить", choices=REMINDER_CHOICES, default=2
    )
    recommendations = models.BooleanField("воркшопы по интересам", default=False)

    class Meta:
        verbose_name = "настройки уведомлений"
        verbose_name_plural = "настройки уведомлений"

    def __str__(self):
        return f"Настройки {self.user.full_name}"
