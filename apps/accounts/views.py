from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.workshops.models import Skill, Workshop

from .forms import LoginForm, RegisterForm
from .models import User


def register(request):
    if request.user.is_authenticated:
        return redirect("workshops:catalog")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        return redirect("workshops:catalog")

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("workshops:catalog")

    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.user)
        return redirect(request.GET.get("next") or "workshops:catalog")

    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect("workshops:catalog")


def mentors(request):
    """Каталог менторов. Карточки приходят из /api/mentors/."""
    return render(request, "pages/mentors.html", {"active_nav": "mentors"})


def mentor_profile(request, pk):
    mentor = get_object_or_404(User.objects.filter(is_mentor=True), pk=pk)
    workshops = (
        Workshop.objects.select_related("skill", "mentor")
        .with_stats()
        .visible_in_catalog()
        .filter(mentor=mentor)
    )
    return render(
        request,
        "pages/mentor_profile.html",
        {
            "mentor": mentor,
            "workshops": workshops,
            "reviews": _mentor_reviews(mentor),
            "is_self": request.user.is_authenticated and request.user.pk == mentor.pk,
            "active_nav": "mentors",
        },
    )


def _mentor_reviews(mentor):
    from apps.enrollments.models import Review

    return (
        Review.objects.filter(workshop__mentor=mentor)
        .select_related("author", "workshop")
        .order_by("-created_at")[:5]
    )


@login_required
def profile(request):
    return render(
        request,
        "pages/profile.html",
        {"skills": Skill.objects.all(), "active_nav": "profile"},
    )


@login_required
def notification_settings(request):
    return render(request, "pages/settings.html", {"active_nav": "profile"})
