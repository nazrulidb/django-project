from django.urls import path
from .views import batch_filter

app_name = "app_departments"
urlpatterns = [
    path("filter/batch/", batch_filter, name="batch_filter"),
]
