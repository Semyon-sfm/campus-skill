from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("config.api_urls")),
    path("", include("apps.workshops.urls")),
    path("", include("apps.enrollments.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.accounts.urls")),
]
