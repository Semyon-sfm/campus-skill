from django.urls import path

from . import views

app_name = "workshops"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("workshops/<int:pk>/", views.workshop_detail, name="detail"),
    path("studio/", views.studio, name="studio"),
    path("studio/new/", views.editor, name="editor_create"),
    path("studio/<int:pk>/edit/", views.editor, name="editor_edit"),
    path("studio/<int:pk>/participants/", views.participants, name="participants"),
]
