from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.db.models import Avg, Count, Q
from django.utils import formats, timezone


class Skill(models.Model):
    """Тег навыка. Цвета и иконка живут здесь, а не в CSS — как в макете."""

    slug = models.SlugField("код", max_length=30, unique=True)
    label = models.CharField("название", max_length=60)
    icon = models.CharField("иконка lucide", max_length=40)
    tag = models.CharField("тег по умолчанию", max_length=40)
    art = models.CharField("надпись на обложке", max_length=20)
    color_bg = models.CharField("цвет фона", max_length=9)
    color_ink = models.CharField("цвет текста", max_length=9)
    order = models.PositiveIntegerField("порядок", default=0)

    class Meta:
        verbose_name = "навык"
        verbose_name_plural = "навыки"
        ordering = ["order", "label"]

    def __str__(self):
        return self.label


def finished_q(prefix=""):
    """Условие «воркшоп завершён» для фильтров, в том числе через связи.

    Завершён — если ментор или админ закрыл его вручную, либо если
    опубликованная встреча уже закончилась по времени. Черновик со
    старой датой завершённым не считается: встречи не было.
    """
    return Q(**{f"{prefix}status": "finished"}) | Q(
        **{f"{prefix}status": "published", f"{prefix}ends_at__lte": timezone.now()}
    )


class WorkshopQuerySet(models.QuerySet):
    def with_stats(self):
        return self.annotate(
            registered_count=Count(
                "enrollments",
                filter=Q(enrollments__status="confirmed"),
                distinct=True,
            ),
            rating_value=Avg("reviews__workshop_score"),
            review_total=Count("reviews", distinct=True),
        )

    def published(self):
        return self.filter(status="published")

    def visible_in_catalog(self):
        return self.published().filter(ends_at__gt=timezone.now())


class Workshop(models.Model):
    FORMAT_CHOICES = [("offline", "Офлайн"), ("online", "Онлайн")]
    LEVEL_CHOICES = [("start", "С нуля"), ("basic", "Есть база")]
    STATUS_CHOICES = [
        ("draft", "Черновик"),
        ("published", "Запись открыта"),
        ("finished", "Воркшоп завершён"),
    ]

    title = models.CharField("название", max_length=90)
    skill = models.ForeignKey(
        Skill, verbose_name="навык", on_delete=models.PROTECT, related_name="workshops"
    )
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="ментор",
        on_delete=models.CASCADE,
        related_name="workshops",
    )
    tag = models.CharField("тег", max_length=40, blank=True)
    art = models.CharField("надпись на обложке", max_length=20, blank=True)

    description = models.TextField("описание", max_length=600)
    outcome = models.TextField("что получится в конце", max_length=600, blank=True)
    program = models.JSONField("программа", default=list)
    requirements = models.TextField("требования к участникам", max_length=600, blank=True)

    date = models.DateField("дата")
    time = models.TimeField("начало")
    duration = models.PositiveIntegerField("длительность, минут", default=90)
    # Хранится, чтобы фильтровать завершённые воркшопы в БД; считается в save().
    ends_at = models.DateTimeField("окончание", editable=False, db_index=True)

    capacity = models.PositiveIntegerField("максимум участников", default=12)
    format = models.CharField("формат", max_length=10, choices=FORMAT_CHOICES, default="offline")
    place = models.CharField("место проведения", max_length=160)
    amount = models.PositiveIntegerField("цена, ₽", default=0)
    level = models.CharField("уровень", max_length=10, choices=LEVEL_CHOICES, default="start")
    requires_approval = models.BooleanField("подтверждать заявки вручную", default=False)
    status = models.CharField("статус", max_length=12, choices=STATUS_CHOICES, default="draft")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WorkshopQuerySet.as_manager()

    class Meta:
        verbose_name = "воркшоп"
        verbose_name_plural = "воркшопы"
        ordering = ["date", "time"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.ends_at = self.starts_at + timedelta(minutes=self.duration)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and {"date", "time", "duration"} & set(update_fields):
            kwargs["update_fields"] = {*update_fields, "ends_at"}
        super().save(*args, **kwargs)

    # --- Производные значения ---

    @property
    def display_tag(self):
        return self.tag or self.skill.tag

    @property
    def display_art(self):
        return self.art or self.skill.art

    @property
    def registered(self):
        value = getattr(self, "registered_count", None)
        if value is None:
            value = self.enrollments.filter(status="confirmed").count()
        return value

    @property
    def free_seats(self):
        return max(0, self.capacity - self.registered)

    @property
    def is_full(self):
        return self.free_seats == 0

    @property
    def starts_at(self):
        naive = datetime.combine(self.date, self.time)
        return timezone.make_aware(naive, timezone.get_current_timezone())

    @property
    def end_time(self):
        return self.ends_at.time()

    @property
    def is_past(self):
        return self.ends_at <= timezone.now()

    @property
    def is_finished(self):
        """То же условие, что finished_q(), — для одного объекта."""
        return self.status == "finished" or (self.status == "published" and self.is_past)

    @property
    def effective_status(self):
        return "finished" if self.is_finished else self.status

    @property
    def rating(self):
        value = getattr(self, "rating_value", None)
        if value is None:
            value = self.reviews.aggregate(value=Avg("workshop_score"))["value"]
        return round(value, 1) if value else None

    @property
    def review_count(self):
        value = getattr(self, "review_total", None)
        if value is None:
            value = self.reviews.count()
        return value

    @property
    def price_label(self):
        return "Бесплатно" if self.amount == 0 else f"{self.amount:,} ₽".replace(",", " ")

    @property
    def day_month_label(self):
        return formats.date_format(self.date, "j E")

    @property
    def end_time_label(self):
        ends = self.ends_at
        label = ends.strftime("%H:%M")
        if ends.date() > self.date:
            label += " (+1 день)"
        return label

    @property
    def short_date_label(self):
        return f"{self.day_month_label} · {self.time:%H:%M}"

    @property
    def full_date_label(self):
        return f"{self.day_month_label} · {self.time:%H:%M}–{self.end_time_label}"

    @property
    def format_label(self):
        return "Онлайн" if self.format == "online" else "Офлайн"

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    @property
    def availability_label(self):
        if self.is_full:
            return "Мест нет · лист ожидания"
        return f"Свободно: {self.free_seats} / {self.capacity}"

    @property
    def level_label(self):
        return "МОЖНО С НУЛЯ" if self.level == "start" else "НУЖНЫ БАЗОВЫЕ ЗНАНИЯ"

    @property
    def duration_label(self):
        minutes = self.duration
        if minutes < 60:
            return f"{minutes} мин"
        hours = minutes / 60
        if minutes % 60 == 0:
            whole = minutes // 60
            if whole % 10 == 1 and whole % 100 != 11:
                word = "час"
            elif whole % 10 in (2, 3, 4) and whole % 100 not in (12, 13, 14):
                word = "часа"
            else:
                word = "часов"
            return f"{whole} {word}"
        return f"{hours:.1f}".replace(".", ",") + " часа"

    def enrollment_for(self, user):
        if not user or not user.is_authenticated:
            return None
        return self.enrollments.filter(participant=user).first()

    def next_status_for(self, user):
        """Какой статус получит участник при записи — логика из макета."""
        if self.is_full:
            return "waitlist"
        if self.requires_approval:
            return "pending"
        return "confirmed"
