from django.contrib import admin

from .models import Notification, NotificationSettings


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "title", "is_read", "created_at"]
    list_filter = ["is_read"]
    search_fields = ["recipient__full_name", "title", "body"]
    autocomplete_fields = ["recipient", "workshop"]


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ["user", "status_changes", "reminders", "reminder_hours",
                    "recommendations"]
    search_fields = ["user__full_name", "user__email"]
    autocomplete_fields = ["user"]
