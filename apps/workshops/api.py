from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.serializers import MentorDetailSerializer
from apps.enrollments.models import Enrollment
from apps.enrollments.serializers import ParticipantRowSerializer
from apps.notifications.services import notify

from .models import Skill, Workshop
from .serializers import (
    MentorCardSerializer,
    SkillSerializer,
    WorkshopCardSerializer,
    WorkshopWriteSerializer,
)


class IsMentorOwnerOrReadOnly(permissions.BasePermission):
    message = "Управлять воркшопом может только его ментор."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.mentor_id == request.user.id


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    pagination_class = None
    lookup_field = "slug"


class WorkshopViewSet(viewsets.ModelViewSet):
    """Каталог и CRUD воркшопов.

    GET /api/workshops/?skill=&q=&format=&date=&price=&level=&limit=&offset=
    """

    permission_classes = [IsMentorOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return WorkshopWriteSerializer
        return WorkshopCardSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["enrollment_map"] = {}
        return context

    def _base_queryset(self):
        return (
            Workshop.objects.select_related("skill", "mentor")
            .with_stats()
            .order_by("date", "time")
        )

    def get_queryset(self):
        queryset = self._base_queryset()
        if self.action != "list":
            return queryset
        return self._apply_catalog_filters(queryset.visible_in_catalog())

    def _apply_catalog_filters(self, queryset):
        params = self.request.query_params

        skill = params.get("skill")
        if skill:
            queryset = queryset.filter(skill__slug=skill)

        mentor = params.get("mentor")
        if mentor:
            queryset = queryset.filter(mentor_id=mentor)

        query = (params.get("q") or "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(tag__icontains=query)
                | Q(skill__label__icontains=query)
                | Q(mentor__full_name__icontains=query)
            )

        fmt = params.get("format")
        if fmt in ("online", "offline"):
            queryset = queryset.filter(format=fmt)

        level = params.get("level")
        if level in ("start", "basic"):
            queryset = queryset.filter(level=level)

        price = params.get("price")
        if price == "free":
            queryset = queryset.filter(amount=0)
        elif price == "paid":
            queryset = queryset.filter(amount__gt=0)

        # «Ближайшие» = до конца недели от сегодня, как в макете (две корзины).
        date_bucket = params.get("date")
        if date_bucket:
            edge = timezone.localdate() + timedelta(days=5)
            if date_bucket == "week":
                queryset = queryset.filter(date__lte=edge)
            elif date_bucket == "later":
                queryset = queryset.filter(date__gt=edge)

        return queryset.distinct()

    def _fill_enrollment_map(self, workshops, context):
        user = self.request.user
        if not user.is_authenticated:
            return
        ids = [workshop.pk for workshop in workshops]
        context["enrollment_map"] = {
            enrollment.workshop_id: enrollment
            for enrollment in Enrollment.objects.filter(
                participant=user, workshop_id__in=ids
            )
        }

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        items = page if page is not None else list(queryset)

        context = self.get_serializer_context()
        self._fill_enrollment_map(items, context)
        serializer = WorkshopCardSerializer(items, many=True, context=context)

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        workshop = self.get_object()
        context = self.get_serializer_context()
        self._fill_enrollment_map([workshop], context)
        return Response(WorkshopCardSerializer(workshop, context=context).data)

    def perform_destroy(self, instance):
        if instance.status == "published" and instance.registered:
            # Нельзя тихо удалить встречу, на которую уже записались люди.
            raise PermissionDenied(
                "На воркшоп уже записались участники. Сначала отмените встречу."
            )
        instance.delete()

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        """Список воркшопов текущего ментора для кабинета."""
        order = {"published": 0, "draft": 1, "finished": 2}
        workshops = sorted(
            self._base_queryset().filter(mentor=request.user),
            key=lambda w: (order.get(w.status, 9), w.date, w.time),
        )
        context = self.get_serializer_context()
        return Response(WorkshopCardSerializer(workshops, many=True, context=context).data)

    @action(detail=True, methods=["get"])
    def related(self, request, pk=None):
        workshop = self.get_object()
        queryset = (
            self._base_queryset()
            .visible_in_catalog()
            .filter(skill=workshop.skill)
            .exclude(pk=workshop.pk)[:3]
        )
        items = list(queryset)
        context = self.get_serializer_context()
        self._fill_enrollment_map(items, context)
        return Response(WorkshopCardSerializer(items, many=True, context=context).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        workshop = self.get_object()
        if workshop.mentor_id != request.user.id:
            return Response({"detail": "Это не ваш воркшоп."}, status=status.HTTP_403_FORBIDDEN)
        workshop.status = "published"
        workshop.save(update_fields=["status", "updated_at"])
        return Response(WorkshopCardSerializer(workshop, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        """Запись на воркшоп. Статус выбирается как в макете."""
        workshop = self.get_object()

        if workshop.status != "published":
            return Response(
                {"detail": "Запись на этот воркшоп закрыта."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if workshop.mentor_id == request.user.id:
            return Response(
                {"detail": "Нельзя записаться на свой воркшоп."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = workshop.enrollment_for(request.user)
        if existing:
            return Response(
                {
                    "detail": "Ты уже записан на этот воркшоп.",
                    "status": existing.status,
                    "status_label": existing.status_label,
                },
                status=status.HTTP_409_CONFLICT,
            )

        enrollment = Enrollment.objects.create(
            workshop=workshop,
            participant=request.user,
            status=workshop.next_status_for(request.user),
        )
        notify(
            request.user,
            enrollment.status_label,
            f"{workshop.title} · {workshop.full_date_label}",
            workshop=workshop,
        )
        notify(
            workshop.mentor,
            "Новая запись на воркшоп",
            f"{request.user.full_name} · {workshop.title} · {enrollment.status_label}",
            workshop=workshop,
        )
        return Response(
            {
                "id": enrollment.pk,
                "status": enrollment.status,
                "status_label": enrollment.status_label,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def participants(self, request, pk=None):
        """Список участников для кабинета ментора, с поиском по имени и группе."""
        workshop = self.get_object()
        if workshop.mentor_id != request.user.id:
            return Response({"detail": "Это не ваш воркшоп."}, status=status.HTTP_403_FORBIDDEN)

        enrollments = workshop.enrollments.select_related("participant").order_by(
            "participant__full_name"
        )
        query = (request.query_params.get("q") or "").strip()
        if query:
            enrollments = enrollments.filter(
                Q(participant__full_name__icontains=query)
                | Q(participant__study_group__icontains=query)
            )
        return Response(
            {
                "workshop": {
                    "id": workshop.pk,
                    "title": workshop.title,
                    "meta": f"{workshop.full_date_label} · {workshop.place}",
                    "availability_label": workshop.availability_label,
                },
                "results": ParticipantRowSerializer(enrollments, many=True).data,
            }
        )


class MentorViewSet(viewsets.ReadOnlyModelViewSet):
    """Каталог менторов."""

    pagination_class = None

    def get_queryset(self):
        return User.objects.filter(is_mentor=True).prefetch_related("workshops__skill")

    def get_serializer_class(self):
        return MentorDetailSerializer if self.action == "retrieve" else MentorCardSerializer
