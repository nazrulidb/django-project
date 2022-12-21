from django.urls import path

from .override_views import index, create, edit

app_name = "students"
urlpatterns = [
    path("", index, name="index"),
    path("add/", create, name="add"),
    path("<str:user_id>/", edit, name="edit"),
    # path("<str:user_id>/delete/", delete, name="delete"),
]
