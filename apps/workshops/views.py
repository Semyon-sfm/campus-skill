from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.enrollments.models import Review

from .models import Skill, Workshop


def catalog(request):
    """Каркас каталога. Сетка карточек наполняется через /api/workshops/."""
    return render(
        request,
        "pages/catalog.html",
        {
            "skills": Skill.objects.all(),
            "active_nav": "catalog",
        },
    )


def workshop_detail(request, pk):
    workshop = get_object_or_404(
        Workshop.objects.select_related("skill", "mentor").with_stats(), pk=pk
    )

    if workshop.status == "draft" and workshop.mentor_id != request.user.id:
        # Черновик видит только его автор.
        return render(request, "pages/draft_hidden.html", {"workshop": workshop}, status=404)

    enrollment = workshop.enrollment_for(request.user)
    reviews = workshop.reviews.select_related("author").all()

    is_owner = request.user.is_authenticated and workshop.mentor_id == request.user.id
    action = _detail_action(workshop, enrollment, is_owner)

    return render(
        request,
        "pages/workshop_detail.html",
        {
            "workshop": workshop,
            "enrollment": enrollment,
            "reviews": reviews,
            "is_owner": is_owner,
            "action": action,
            "active_nav": "studio" if is_owner else "catalog",
        },
    )


def _detail_action(workshop, enrollment, is_owner):
    """Что показывает главная кнопка на карточке воркшопа — логика из макета."""
    if workshop.is_finished:
        return {"label": "Воркшоп завершён", "note": "Отзывы доступны после участия.",
                "disabled": True, "kind": "none"}

    if is_owner:
        if workshop.status == "draft":
            return {"label": "Редактировать воркшоп", "note": "Управление своим воркшопом.",
                    "disabled": False, "kind": "edit"}
        return {"label": "Список участников", "note": "Управление своим воркшопом.",
                "disabled": False, "kind": "participants"}

    if workshop.status == "draft":
        return {"label": "Воркшоп ещё не опубликован",
                "note": "Запись откроется после публикации.",
                "disabled": True, "kind": "none"}

    if enrollment:
        return {"label": "Открыть в моём обучении", "note": enrollment.status_label,
                "disabled": False, "kind": "learning"}

    if workshop.is_full:
        return {"label": "Встать в лист ожидания",
                "note": "Сообщим, если освободится место.",
                "disabled": False, "kind": "enroll"}

    if workshop.requires_approval:
        return {"label": "Подать заявку",
                "note": "Ментор подтвердит участие после заявки.",
                "disabled": False, "kind": "enroll"}

    return {"label": "Записаться", "note": "Подтверждение сразу после записи.",
            "disabled": False, "kind": "enroll"}


@login_required
def studio(request):
    """Кабинет ментора. Список воркшопов приходит из /api/workshops/mine/."""
    if not request.user.is_mentor:
        return redirect("accounts:profile")
    return render(request, "pages/studio.html", {"active_nav": "studio"})


@login_required
def editor(request, pk=None):
    workshop = None
    if pk is not None:
        workshop = get_object_or_404(Workshop.objects.with_stats(), pk=pk, mentor=request.user)

    return render(
        request,
        "pages/editor.html",
        {
            "workshop": workshop,
            "skills": Skill.objects.all(),
            "active_nav": "studio",
        },
    )


@login_required
def participants(request, pk):
    workshop = get_object_or_404(
        Workshop.objects.select_related("skill").with_stats(), pk=pk, mentor=request.user
    )
    return render(
        request,
        "pages/participants.html",
        {"workshop": workshop, "active_nav": "studio"},
    )
