from django.urls import reverse
from rest_framework import serializers

from apps.accounts.models import User

from .models import Skill, Workshop


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["slug", "label", "icon", "tag", "art", "color_bg", "color_ink"]


class MentorBriefSerializer(serializers.ModelSerializer):
    initials = serializers.CharField(read_only=True)
    rating = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "full_name", "initials", "experience", "rating", "url"]

    def get_rating(self, obj):
        value = obj.mentor_rating
        return f"{value}".replace(".", ",") if value else None

    def get_url(self, obj):
        return reverse("accounts:mentor_profile", args=[obj.pk])


class MentorCardSerializer(MentorBriefSerializer):
    skill = serializers.SerializerMethodField()
    format_label = serializers.CharField(source="teaching_format_label", read_only=True)
    price_label = serializers.CharField(read_only=True)
    review_count = serializers.IntegerField(source="mentor_review_count", read_only=True)

    class Meta(MentorBriefSerializer.Meta):
        fields = MentorBriefSerializer.Meta.fields + [
            "skill",
            "format_label",
            "price_label",
            "review_count",
            "bio",
            "study_group",
        ]

    def get_skill(self, obj):
        workshop = obj.workshops.select_related("skill").first()
        return workshop.skill.label if workshop else "Навык уточняется"


class WorkshopCardSerializer(serializers.ModelSerializer):
    """Плоский JSON ровно под data-атрибуты карточки из макета."""

    skill = SkillSerializer(read_only=True)
    mentor = MentorBriefSerializer(read_only=True)

    tag = serializers.CharField(source="display_tag", read_only=True)
    art = serializers.CharField(source="display_art", read_only=True)
    format_label = serializers.CharField(read_only=True)
    date_label = serializers.CharField(source="short_date_label", read_only=True)
    duration_label = serializers.CharField(read_only=True)
    price_label = serializers.CharField(read_only=True)
    availability_label = serializers.CharField(read_only=True)
    registered = serializers.IntegerField(read_only=True)
    free_seats = serializers.IntegerField(read_only=True)
    rating = serializers.SerializerMethodField()
    review_count = serializers.IntegerField(read_only=True)
    my_status = serializers.SerializerMethodField()
    my_status_label = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Workshop
        fields = [
            "id",
            "title",
            "description",
            "skill",
            "mentor",
            "tag",
            "art",
            "format",
            "format_label",
            "date",
            "date_label",
            "duration_label",
            "price_label",
            "amount",
            "availability_label",
            "registered",
            "free_seats",
            "capacity",
            "rating",
            "review_count",
            "status",
            "my_status",
            "my_status_label",
            "url",
        ]

    def get_rating(self, obj):
        value = obj.rating
        return f"{value}".replace(".", ",") if value else None

    def _enrollment(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        cache = self.context.get("enrollment_map")
        if cache is not None:
            return cache.get(obj.pk)
        return obj.enrollment_for(request.user)

    def get_my_status(self, obj):
        enrollment = self._enrollment(obj)
        return enrollment.status if enrollment else None

    def get_my_status_label(self, obj):
        enrollment = self._enrollment(obj)
        return enrollment.status_label if enrollment else None

    def get_url(self, obj):
        return reverse("workshops:detail", args=[obj.pk])


class WorkshopWriteSerializer(serializers.ModelSerializer):
    """Форма редактора воркшопа. Программа приходит текстом, по пункту на строку."""

    program = serializers.CharField(allow_blank=False)
    skill = serializers.SlugRelatedField(slug_field="slug", queryset=Skill.objects.all())
    intent = serializers.ChoiceField(
        choices=["draft", "publish"], write_only=True, required=False, default="draft"
    )

    class Meta:
        model = Workshop
        fields = [
            "id",
            "title",
            "skill",
            "level",
            "description",
            "program",
            "requirements",
            "date",
            "time",
            "duration",
            "capacity",
            "format",
            "amount",
            "place",
            "requires_approval",
            "intent",
        ]

    def validate_program(self, value):
        items = [line.strip() for line in value.splitlines() if line.strip()]
        if not items:
            raise serializers.ValidationError("Добавь хотя бы один пункт программы.")
        return items

    def validate_capacity(self, value):
        if self.instance and value < self.instance.registered:
            raise serializers.ValidationError(
                f"Уже записано {self.instance.registered} участников — "
                f"вместимость не может быть меньше."
            )
        return value

    def _resolve_status(self, intent):
        if intent == "publish":
            return "published"
        if self.instance and self.instance.status == "published":
            # Опубликованный воркшоп не возвращаем в черновики при обычном сохранении.
            return "published"
        return "draft"

    def create(self, validated_data):
        intent = validated_data.pop("intent", "draft")
        validated_data["status"] = self._resolve_status(intent)
        validated_data["outcome"] = validated_data.get("description", "")
        validated_data["mentor"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        intent = validated_data.pop("intent", "draft")
        validated_data["status"] = self._resolve_status(intent)
        validated_data["outcome"] = validated_data.get("description", instance.outcome)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return WorkshopCardSerializer(instance, context=self.context).data
