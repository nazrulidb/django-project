from django.apps import AppConfig
from wagtail.users.apps import WagtailUsersAppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"


class CustomUsersAppConfig(WagtailUsersAppConfig):
    group_viewset = "users.viewsets.GroupViewSet"
