from django.contrib import admin

from .models import Enrollment, Review


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["workshop", "participant", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["workshop__title", "participant__full_name"]
    autocomplete_fields = ["participant"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["workshop", "author", "workshop_score", "mentor_score", "created_at"]
    list_filter = ["workshop_score", "mentor_score"]
    search_fields = ["workshop__title", "author__full_name", "text"]
    autocomplete_fields = ["author"]
