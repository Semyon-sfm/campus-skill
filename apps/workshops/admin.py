from django.contrib import admin

from .models import Skill, Workshop


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["label", "slug", "icon", "order"]
    ordering = ["order"]


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ["title", "skill", "mentor", "date", "time", "status", "capacity"]
    list_filter = ["status", "format", "level", "skill"]
    search_fields = ["title", "description", "mentor__full_name"]
    date_hierarchy = "date"
    autocomplete_fields = ["mentor"]
