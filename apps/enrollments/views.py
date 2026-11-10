from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.workshops.models import Workshop

from .models import Enrollment, Review


@login_required
def enroll(request, pk):
    """Экран «Осталось проверить детали» перед записью."""
    workshop = get_object_or_404(
        Workshop.objects.select_related("skill", "mentor").with_stats(),
        pk=pk,
        status="published",
    )

    if workshop.enrollment_for(request.user):
        return redirect("enrollments:learning")
    if workshop.mentor_id == request.user.id:
        return redirect("workshops:detail", pk=pk)

    waiting = workshop.is_full
    if waiting:
        heading = "Встать в лист ожидания?"
        copy = "Свободных мест нет. Сообщим, если место освободится."
        confirm = "Встать в лист ожидания"
    elif workshop.requires_approval:
        heading = "Отправить заявку ментору"
        copy = "Ментор подтвердит участие — статус появится в «Моём обучении»."
        confirm = "Отправить заявку"
    else:
        heading = "Осталось проверить детали"
        copy = "Проверь данные встречи — место закрепим сразу после записи."
        confirm = "Записаться на воркшоп"

    return render(
        request,
        "pages/enrollment.html",
        {
            "workshop": workshop,
            "heading": heading,
            "copy": copy,
            "confirm_label": confirm,
            "waiting": waiting,
            "active_nav": "catalog",
        },
    )


@login_required
def enroll_success(request, pk):
    workshop = get_object_or_404(Workshop.objects.select_related("skill"), pk=pk)
    enrollment = get_object_or_404(Enrollment, workshop=workshop, participant=request.user)

    messages = {
        "confirmed": (
            "УЧАСТИЕ ПОДТВЕРЖДЕНО",
            "Увидимся на воркшопе!",
            "Встреча появилась в «Моём обучении». Здесь будут детали и напоминание.",
        ),
        "waitlist": (
            "ЛИСТ ОЖИДАНИЯ",
            "Ты в списке ожидания",
            "Если освободится место, в личном кабинете появится уведомление.",
        ),
        "pending": (
            "ЗАЯВКА ОТПРАВЛЕНА",
            "Ждём ответа ментора",
            "Заявка появилась в «Моём обучении». Об изменении статуса сообщим в уведомлениях.",
        ),
    }
    label, title, copy = messages.get(enrollment.status, messages["confirmed"])

    return render(
        request,
        "pages/enroll_success.html",
        {
            "workshop": workshop,
            "enrollment": enrollment,
            "success_label": label,
            "success_title": title,
            "success_copy": copy,
            "active_nav": "catalog",
        },
    )


@login_required
def learning(request):
    """«Моё обучение». Табы и списки наполняются через /api/enrollments/."""
    tab = request.GET.get("tab", "upcoming")
    if tab not in ("upcoming", "history", "waitlist"):
        tab = "upcoming"
    return render(
        request,
        "pages/learning.html",
        {"active_tab": tab, "active_nav": "learning"},
    )


@login_required
def cancel(request, pk):
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("workshop__skill", "workshop__mentor"),
        pk=pk,
        participant=request.user,
    )

    headings = {
        "waitlist": ("Покинуть лист ожидания?",
                     "Ты выйдешь из списка ожидания этого воркшопа.",
                     "Покинуть лист ожидания"),
        "pending": ("Отозвать заявку?",
                    "Ментор увидит, что заявка отозвана.",
                    "Отозвать заявку"),
        "confirmed": ("Отменить участие?",
                      "Твоё место станет доступно другому участнику. "
                      "При наличии мест можно будет записаться снова.",
                      "Отменить запись"),
    }
    heading, copy, confirm = headings.get(enrollment.status, headings["confirmed"])

    return render(
        request,
        "pages/cancel.html",
        {
            "enrollment": enrollment,
            "workshop": enrollment.workshop,
            "heading": heading,
            "copy": copy,
            "confirm_label": confirm,
            "active_nav": "learning",
        },
    )


@login_required
def review(request, pk):
    workshop = get_object_or_404(
        Workshop.objects.select_related("skill", "mentor"), pk=pk
    )
    enrollment = get_object_or_404(
        Enrollment, workshop=workshop, participant=request.user, status="confirmed"
    )

    if not (workshop.status == "finished" or workshop.is_past):
        return redirect("enrollments:learning")

    existing = Review.objects.filter(workshop=workshop, author=request.user).first()

    return render(
        request,
        "pages/review.html",
        {
            "workshop": workshop,
            "enrollment": enrollment,
            "existing": existing,
            "active_nav": "learning",
        },
    )
