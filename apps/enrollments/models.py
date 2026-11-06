from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ("confirmed", "Участие подтверждено"),
        ("pending", "Ждёт подтверждения"),
        ("waitlist", "В листе ожидания"),
    ]

    workshop = models.ForeignKey(
        "workshops.Workshop",
        verbose_name="воркшоп",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="участник",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    status = models.CharField("статус", max_length=12, choices=STATUS_CHOICES, default="confirmed")
    cancel_reason = models.CharField("причина отмены", max_length=60, blank=True)
    reminded_at = models.DateTimeField("напоминание отправлено", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "запись"
        verbose_name_plural = "записи"
        ordering = ["workshop__date", "workshop__time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workshop", "participant"], name="unique_enrollment_per_workshop"
            )
        ]

    def __str__(self):
        return f"{self.participant.full_name} → {self.workshop.title} ({self.status})"

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


class Review(models.Model):
    workshop = models.ForeignKey(
        "workshops.Workshop",
        verbose_name="воркшоп",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="автор",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    workshop_score = models.PositiveSmallIntegerField(
        "оценка воркшопа", validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    mentor_score = models.PositiveSmallIntegerField(
        "оценка ментора", validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField("текст отзыва", max_length=1200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "отзыв"
        verbose_name_plural = "отзывы"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["workshop", "author"], name="unique_review_per_workshop"
            )
        ]

    def __str__(self):
        return f"{self.author.full_name} о «{self.workshop.title}»"
