from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.coach_list,
        name="coach_list",
    ),

    path(
        "create/",
        views.coach_create,
        name="coach_create",
    ),

    path(
        "<int:pk>/edit/",
        views.coach_edit,
        name="coach_edit",
    ),

    path(
        "<int:pk>/delete/",
        views.coach_delete,
        name="coach_delete",
    ),

    path(
        "simulate/",
        views.simulate,
        name="simulate",
    ),
]
