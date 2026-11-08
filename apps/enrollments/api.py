from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from apps.notifications.services import notify

from .models import Enrollment, Review
from .serializers import EnrollmentRowSerializer, ReviewSerializer


class EnrollmentViewSet(
    mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """Записи текущего пользователя.

    GET /api/enrollments/?tab=upcoming|history|waitlist
    DELETE /api/enrollments/<id>/   — отмена записи
    """

    serializer_class = EnrollmentRowSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return (
            Enrollment.objects.filter(participant=self.request.user)
            .select_related("workshop__skill", "workshop__mentor")
            .order_by("workshop__date", "workshop__time")
        )

    def list(self, request, *args, **kwargs):
        tab = request.query_params.get("tab", "upcoming")
        now = timezone.now()
        queryset = self.get_queryset()

        if tab == "waitlist":
            queryset = queryset.filter(status="waitlist")
        elif tab == "history":
            queryset = (
                queryset.exclude(status="waitlist")
                .filter(Q(workshop__status="finished") | Q(workshop__date__lt=now.date()))
                .order_by("-workshop__date", "-workshop__time")
            )
        else:
            queryset = (
                queryset.exclude(status="waitlist")
                .exclude(workshop__status="finished")
                .filter(workshop__date__gte=now.date())
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        enrollment = self.get_object()
        workshop = enrollment.workshop
        previous = enrollment.status

        reason = (request.query_params.get("reason") or "").strip()[:60]
        titles = {
            "waitlist": "Выход из листа ожидания",
            "pending": "Заявка отозвана",
            "confirmed": "Запись отменена",
        }
        title = titles.get(previous, "Запись отменена")

        enrollment.delete()

        notify(
            request.user,
            title,
            f"{workshop.title} · {workshop.full_date_label}",
            workshop=workshop,
        )
        notify(
            workshop.mentor,
            "Изменение записи на воркшоп",
            f"{request.user.full_name} · {workshop.title} · {title}"
            + (f" · {reason}" if reason else ""),
            workshop=workshop,
        )
        self._promote_from_waitlist(workshop)

        flash = {
            "waitlist": "Ты вышел из листа ожидания.",
            "pending": "Заявка отозвана.",
            "confirmed": "Запись отменена. Место снова доступно в каталоге.",
        }.get(previous, "Запись отменена.")
        return Response({"detail": title, "flash": flash}, status=status.HTTP_200_OK)

    def _promote_from_waitlist(self, workshop):
        """Освободилось место — двигаем первого из листа ожидания."""
        if workshop.free_seats <= 0:
            return
        candidate = (
            workshop.enrollments.filter(status="waitlist").order_by("created_at").first()
        )
        if not candidate:
            return
        candidate.status = "pending" if workshop.requires_approval else "confirmed"
        candidate.save(update_fields=["status"])
        notify(
            candidate.participant,
            "Освободилось место",
            f"{workshop.title} · {workshop.full_date_label} · {candidate.status_label}",
            workshop=workshop,
        )


class EnrollmentStatusViewSet(viewsets.GenericViewSet):
    """Ментор подтверждает или отклоняет заявку участника."""

    permission_classes = [permissions.IsAuthenticated]
    queryset = Enrollment.objects.select_related("workshop", "participant")

    def partial_update(self, request, pk=None):
        enrollment = self.get_object()
        if enrollment.workshop.mentor_id != request.user.id:
            return Response(
                {"detail": "Это не ваш воркшоп."}, status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get("status")
        if new_status not in dict(Enrollment.STATUS_CHOICES):
            return Response(
                {"detail": "Неизвестный статус."}, status=status.HTTP_400_BAD_REQUEST
            )

        enrollment.status = new_status
        enrollment.save(update_fields=["status"])
        notify(
            enrollment.participant,
            enrollment.status_label,
            f"{enrollment.workshop.title} · {enrollment.workshop.full_date_label}",
            workshop=enrollment.workshop,
        )
        return Response(
            {"id": enrollment.pk, "status": enrollment.status, "status_label": enrollment.status_label}
        )


class ReviewViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        queryset = Review.objects.select_related("author", "workshop")
        workshop = self.request.query_params.get("workshop")
        if workshop:
            queryset = queryset.filter(workshop_id=workshop)
        return queryset

    def perform_create(self, serializer):
        review = serializer.save()
        notify(
            review.workshop.mentor,
            "Новый отзыв о воркшопе",
            f"{review.author.full_name} · {review.workshop.title} · "
            f"★ {review.workshop_score}",
            workshop=review.workshop,
        )
