from django.urls import reverse
from rest_framework import serializers

from apps.notifications.models import NotificationSettings
from apps.workshops.models import Skill

from .models import User


class SkillChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["slug", "label", "icon"]


class ProfileSerializer(serializers.ModelSerializer):
    initials = serializers.CharField(read_only=True)
    interests = serializers.SlugRelatedField(
        slug_field="slug", queryset=Skill.objects.all(), many=True, required=False
    )
    role_label = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "study_group",
            "bio",
            "experience",
            "is_mentor",
            "initials",
            "interests",
            "role_label",
        ]
        read_only_fields = ["email", "is_mentor"]

    def get_role_label(self, obj):
        return "Ментор" if obj.is_mentor else "Участник"

    def validate_full_name(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Имя слишком короткое.")
        return value


class InterestsSerializer(serializers.Serializer):
    interests = serializers.SlugRelatedField(
        slug_field="slug", queryset=Skill.objects.all(), many=True
    )

    def update(self, instance, validated_data):
        instance.interests.set(validated_data["interests"])
        return instance


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = ["status_changes", "reminders", "reminder_hours", "recommendations"]


class MentorDetailSerializer(serializers.ModelSerializer):
    """Публичный профиль ментора."""

    initials = serializers.CharField(read_only=True)
    rating = serializers.SerializerMethodField()
    review_count = serializers.IntegerField(source="mentor_review_count", read_only=True)
    format_label = serializers.CharField(source="teaching_format_label", read_only=True)
    price_label = serializers.CharField(read_only=True)
    skill = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "initials",
            "experience",
            "bio",
            "study_group",
            "rating",
            "review_count",
            "format_label",
            "price_label",
            "skill",
            "url",
        ]

    def get_rating(self, obj):
        value = obj.mentor_rating
        return f"{value}".replace(".", ",") if value else None

    def get_skill(self, obj):
        workshop = obj.workshops.select_related("skill").first()
        return workshop.skill.label if workshop else "Навык уточняется"

    def get_url(self, obj):
        return reverse("accounts:mentor_profile", args=[obj.pk])


class RegisterSerializer(serializers.ModelSerializer):
    """Регистрация: email + пароль, без валидаторов пароля — по требованию заказчика."""

    password = serializers.CharField(write_only=True, min_length=1)

    class Meta:
        model = User
        fields = ["email", "full_name", "study_group", "password"]

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Этот email уже зарегистрирован.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)
