from django.urls import reverse
from rest_framework import serializers

from apps.workshops.models import Workshop

from .models import Enrollment, Review


class ParticipantRowSerializer(serializers.ModelSerializer):
    """Строка в списке участников у ментора."""

    name = serializers.CharField(source="participant.full_name", read_only=True)
    group = serializers.CharField(source="participant.study_group", read_only=True)
    initials = serializers.CharField(source="participant.initials", read_only=True)
    status_label = serializers.CharField(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "name", "group", "initials", "status", "status_label"]


class EnrollmentRowSerializer(serializers.ModelSerializer):
    """Строка в «Моём обучении» — под data-атрибуты карточки из макета."""

    workshop_id = serializers.IntegerField(source="workshop.pk", read_only=True)
    title = serializers.CharField(source="workshop.title", read_only=True)
    day = serializers.SerializerMethodField()
    month = serializers.SerializerMethodField()
    meta = serializers.SerializerMethodField()
    extra = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    workshop_url = serializers.SerializerMethodField()
    cancel_url = serializers.SerializerMethodField()
    review_url = serializers.SerializerMethodField()
    can_review = serializers.SerializerMethodField()
    has_review = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "workshop_id",
            "title",
            "day",
            "month",
            "meta",
            "extra",
            "status",
            "status_label",
            "state",
            "workshop_url",
            "cancel_url",
            "review_url",
            "can_review",
            "has_review",
        ]

    MONTHS = [
        "янв", "фев", "мар", "апр", "мая", "июн",
        "июл", "авг", "сен", "окт", "ноя", "дек",
    ]

    def get_day(self, obj):
        return str(obj.workshop.date.day)

    def get_month(self, obj):
        return self.MONTHS[obj.workshop.date.month - 1]

    def get_meta(self, obj):
        workshop = obj.workshop
        return f"{workshop.full_date_label} · {workshop.place}"

    def get_extra(self, obj):
        workshop = obj.workshop
        return f"{workshop.mentor.full_name} · {workshop.price_label}"

    def _is_finished(self, obj):
        return obj.workshop.is_finished

    def get_status_label(self, obj):
        if self._is_finished(obj):
            return "Воркшоп завершён"
        return obj.status_label

    def get_state(self, obj):
        return "finished" if self._is_finished(obj) else obj.status

    def get_workshop_url(self, obj):
        return reverse("workshops:detail", args=[obj.workshop_id])

    def get_cancel_url(self, obj):
        return reverse("enrollments:cancel", args=[obj.pk])

    def get_review_url(self, obj):
        return reverse("enrollments:review", args=[obj.workshop_id])

    def get_has_review(self, obj):
        return Review.objects.filter(
            workshop_id=obj.workshop_id, author_id=obj.participant_id
        ).exists()

    def get_can_review(self, obj):
        return (
            self._is_finished(obj)
            and obj.status == "confirmed"
            and not self.get_has_review(obj)
        )


class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    author_initials = serializers.CharField(source="author.initials", read_only=True)
    workshop = serializers.PrimaryKeyRelatedField(queryset=Workshop.objects.all())

    class Meta:
        model = Review
        fields = [
            "id",
            "workshop",
            "workshop_score",
            "mentor_score",
            "text",
            "author_name",
            "author_initials",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_text(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("Напиши хотя бы пару предложений.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        workshop = attrs["workshop"]

        enrollment = Enrollment.objects.filter(
            workshop=workshop, participant=request.user, status="confirmed"
        ).first()
        if not enrollment:
            raise serializers.ValidationError(
                "Отзыв можно оставить только о воркшопе, в котором ты участвовал."
            )
        if not workshop.is_finished:
            raise serializers.ValidationError("Воркшоп ещё не прошёл.")
        if Review.objects.filter(workshop=workshop, author=request.user).exists():
            raise serializers.ValidationError("Ты уже оставил отзыв об этом воркшопе.")
        return attrs

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)
