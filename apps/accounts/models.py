from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


def initials_from_name(name):
    parts = [part for part in str(name).split() if part]
    return "".join(part[0].upper() for part in parts[:2]) or "CS"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Нужен email")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("full_name", "Администратор")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Один пользователь — обе роли: участник всегда, ментор по флагу."""

    email = models.EmailField("email", unique=True)
    full_name = models.CharField("имя и фамилия", max_length=70)
    study_group = models.CharField("учебная группа", max_length=30, blank=True)
    bio = models.TextField("о себе", max_length=700, blank=True)

    is_mentor = models.BooleanField("ментор", default=False)
    experience = models.CharField("опыт и специализация", max_length=150, blank=True)

    interests = models.ManyToManyField(
        "workshops.Skill",
        verbose_name="интересующие навыки",
        related_name="interested_users",
        blank=True,
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def initials(self):
        return initials_from_name(self.full_name)

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email

    # --- Витрина ментора: считаем из его воркшопов, а не храним текстом ---

    def mentor_workshops(self):
        return self.workshops.filter(status__in=("published", "finished"))

    @property
    def teaching_format_label(self):
        formats = set(self.mentor_workshops().values_list("format", flat=True))
        if formats == {"online", "offline"}:
            return "Онлайн и офлайн"
        if formats == {"online"}:
            return "Онлайн"
        if formats == {"offline"}:
            return "Офлайн"
        return "Формат уточняется"

    @property
    def price_label(self):
        amounts = list(self.mentor_workshops().values_list("amount", flat=True))
        if not amounts:
            return "Воркшопов пока нет"
        paid = [amount for amount in amounts if amount > 0]
        if not paid:
            return "Бесплатные воркшопы"
        return f"От {min(paid)} ₽ за встречу"

    @property
    def mentor_rating(self):
        from apps.enrollments.models import Review

        value = Review.objects.filter(workshop__mentor=self).aggregate(
            value=models.Avg("mentor_score")
        )["value"]
        return round(value, 1) if value else None

    @property
    def mentor_review_count(self):
        from apps.enrollments.models import Review

        return Review.objects.filter(workshop__mentor=self).count()
