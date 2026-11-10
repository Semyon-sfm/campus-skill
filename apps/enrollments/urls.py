from django.urls import path

from . import views

app_name = "enrollments"

urlpatterns = [
    path("workshops/<int:pk>/enroll/", views.enroll, name="enroll"),
    path("workshops/<int:pk>/enrolled/", views.enroll_success, name="success"),
    path("learning/", views.learning, name="learning"),
    path("learning/<int:pk>/cancel/", views.cancel, name="cancel"),
    path("workshops/<int:pk>/review/", views.review, name="review"),
]
