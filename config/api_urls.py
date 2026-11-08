"""Единая точка входа REST API — всё под /api/."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.api import (
    BecomeMentorView,
    InterestsView,
    NotificationSettingsView,
    ProfileView,
    SkillProgressView,
)
from apps.enrollments.api import EnrollmentStatusViewSet, EnrollmentViewSet, ReviewViewSet
from apps.notifications.api import NotificationViewSet
from apps.workshops.api import MentorViewSet, SkillViewSet, WorkshopViewSet

router = DefaultRouter()
router.register("workshops", WorkshopViewSet, basename="workshop")
router.register("skills", SkillViewSet, basename="skill")
router.register("mentors", MentorViewSet, basename="mentor")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")
router.register("enrollment-status", EnrollmentStatusViewSet, basename="enrollment-status")
router.register("reviews", ReviewViewSet, basename="review")
router.register("notifications", NotificationViewSet, basename="notification")

app_name = "api"

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/interests/", InterestsView.as_view(), name="interests"),
    path("profile/settings/", NotificationSettingsView.as_view(), name="settings"),
    path("profile/become-mentor/", BecomeMentorView.as_view(), name="become-mentor"),
    path("profile/skill-progress/", SkillProgressView.as_view(), name="skill-progress"),
    path("", include(router.urls)),
]
