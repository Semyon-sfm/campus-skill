from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "full_name", "study_group", "is_mentor", "is_staff"]
    list_filter = ["is_mentor", "is_staff", "is_active"]
    search_fields = ["email", "full_name", "study_group"]
    ordering = ["full_name"]
    filter_horizontal = ["interests", "groups", "user_permissions"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профиль", {"fields": ("full_name", "study_group", "bio", "interests")}),
        ("Ментор", {"fields": ("is_mentor", "experience")}),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser", "groups",
                              "user_permissions")}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2"),
        }),
    )
