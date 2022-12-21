from wagtail.core import hooks
from wagtail.admin.menu import MenuItem
from django.urls import path, reverse, include
from django.utils.translation import gettext_lazy as _
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.admin.search import SearchArea
from .wagtail_views import index, create, edit

from users.models import *
from departments.models import Batch
from django.contrib.auth.models import Group
from django.views.decorators.cache import never_cache
from users import urls

add_user_perm = "{0}.add_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
change_user_perm = "{0}.change_{1}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)
delete_user_perm = "{0}.delete_{1}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)


class UsersMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm(add_user_perm)
            or request.user.has_perm(change_user_perm)
            or request.user.has_perm(delete_user_perm)
        )


@hooks.register("register_admin_urls")
def register_custom_users():
    return [
        path("users/", index, name="custom_users"),
       
        path("users/add/", create, name="add"),
        path("users/<str:user_id>/", edit, name="edit"),
        # path("users/", include(urls, namespace="users.urls")),
    ]


class UsersSearchArea(SearchArea):
    def is_shown(self, request):
        return (
            request.user.has_perm(add_user_perm)
            or request.user.has_perm(change_user_perm)
            or request.user.has_perm(delete_user_perm)
        )


@hooks.register("register_admin_search_area")
def register_users_search_area():
    return UsersSearchArea(
        _("Users"),
        reverse("wagtailusers_users:index"),
        name="users_custom",
        icon_name="user",
        order=600,
    )




@hooks.register("construct_settings_menu")
def hide_original_setting_users(request, menu_items):
    if not request.user.id == 1:
        show_only = ["users", "roles"]
        menu_items[:] = [item for item in menu_items if item.name in show_only]

@never_cache
@hooks.register("construct_main_menu")
def remove_main_menu(request, menu_items):
    to_hide = ["images", "explorer", "reports"]
    if not request.user.id == 1:
        menu_items[:] = [item for item in menu_items if not item.name in to_hide]

    print("construct_main_menu")
    print(request.user.role)
    if str(request.user.role) == "Proof Reader of Exam" or str(request.user.role) == "Controller of Exam":
        for menu in menu_items:
            if menu.name == "dashboard":
                for i in menu.menu._registered_menu_items:
                    print(i.label)
                    if i.label == "Batch Upload":
                        
                        if str(request.user.role) == "Proof Reader of Exam":
                            i.label = "Result Review"
                        elif str(request.user.role) == "Controller of Exam":
                            i.label = "Result upload"
                    
        

@hooks.register("after_create_user")
def update_user_group(request, instance):
    print("UPDATE instance GROUP!")

    print(f'prev role {instance.metadata.get("prev_role")}')
    print(f"new role {instance.role}")

    print(request.path)
    if (
        request.path.startswith("/cms/users")
        and instance.role != instance.metadata.get("prev_role")
        and instance.id
    ):

        if str(instance.role) == "Super User":
            CustomUser.objects.filter(id=instance.id).update(is_superuser=True)
        elif (
            instance.metadata.get("prev_role")
            and instance.metadata.get("prev_role") == "Super User"
        ):
            CustomUser.objects.filter(id=instance.id).update(is_superuser=False)
        if (
            instance.metadata.get("prev_role")
            and instance.metadata.get("prev_role") == "Faculty Member"
            and str(instance.role) != "Faculty Member"
        ):
            Batch.objects.filter(assigned_faculty_member=instance).update(
                assigned_faculty_member=None
            )

        group, created = Group.objects.get_or_create(name=str(instance.role))

        instance.groups.set([group])

        # return {'status_code':200}
    if str(instance.role) == "Student":
        print(instance.groups)

        instance.metadata["prev_role"] = str(instance.role)
        a = instance.institute.code
        b = instance.batch.id
        c = instance.batch.degree.id
        d = instance.department.id
        e = instance.suffix
        custom_id = f"{a}-{b}-{c}-{d}-{e}"
        new_format = f"{a}-{b}{c}{d}{e}"

        instance.metadata["formated_id"] = custom_id
        # instance.username = new_format
        print(f"custom_id {custom_id}")
        print(f"new_format {new_format}")
        print("saving...")
      
        instance.save()

    if instance.groups:
        print("HERE ON ELSE")
        if instance.role:

            instance.groups.set([instance.role])
            instance.save()

            # return {'status_code':200}

