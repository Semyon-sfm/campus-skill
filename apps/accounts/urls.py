from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("mentors/", views.mentors, name="mentors"),
    path("mentors/<int:pk>/", views.mentor_profile, name="mentor_profile"),
    path("profile/", views.profile, name="profile"),
    path("profile/settings/", views.notification_settings, name="settings"),
]
