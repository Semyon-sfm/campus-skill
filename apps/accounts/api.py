from django.db.models import Count, Q
from rest_framework import permissions, views
from rest_framework.response import Response

from apps.notifications.services import settings_for
from apps.workshops.models import Skill, finished_q

from .serializers import (
    InterestsSerializer,
    NotificationSettingsSerializer,
    ProfileSerializer,
    SkillChoiceSerializer,
)


class ProfileView(views.APIView):
    """GET/PATCH профиля текущего пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(ProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({**serializer.data, "flash": "Профиль обновлён."})


class InterestsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "available": SkillChoiceSerializer(Skill.objects.all(), many=True).data,
                "selected": list(request.user.interests.values_list("slug", flat=True)),
            }
        )

    def put(self, request):
        serializer = InterestsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)
        return Response(
            {
                "selected": list(request.user.interests.values_list("slug", flat=True)),
                "detail": "Интересы сохранены.",
            }
        )


class NotificationSettingsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(NotificationSettingsSerializer(settings_for(request.user)).data)

    def patch(self, request):
        serializer = NotificationSettingsSerializer(
            settings_for(request.user), data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({**serializer.data, "detail": "Настройки сохранены."})


class BecomeMentorView(views.APIView):
    """Переключатель роли: участник открывает себе кабинет ментора."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.is_mentor = True
        request.user.save(update_fields=["is_mentor"])
        return Response({"is_mentor": True, "detail": "Кабинет ментора открыт."})


class SkillProgressView(views.APIView):
    """«Мои навыки» — прогресс по посещённым воркшопам."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rows = (
            Skill.objects.annotate(
                attended=Count(
                    "workshops__enrollments",
                    filter=Q(
                        workshops__enrollments__participant=request.user,
                        workshops__enrollments__status="confirmed",
                    )
                    & finished_q("workshops__"),
                    distinct=True,
                )
            )
            .filter(attended__gt=0)
            .order_by("-attended", "order")
        )
        return Response(
            [
                {
                    "slug": skill.slug,
                    "label": skill.label,
                    "icon": skill.icon,
                    "attended": skill.attended,
                    "attended_label": _plural(
                        skill.attended, "воркшоп", "воркшопа", "воркшопов"
                    ),
                }
                for skill in rows
            ]
        )


def _plural(number, one, few, many):
    tail_hundred = number % 100
    tail = number % 10
    if 11 <= tail_hundred <= 14:
        word = many
    elif tail == 1:
        word = one
    elif 2 <= tail <= 4:
        word = few
    else:
        word = many
    return f"{number} {word}"
