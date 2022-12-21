from django.urls import path
from .views import publish

urlpatterns = [
    path("publish/<int:id>/", publish, name="publish"),
]
