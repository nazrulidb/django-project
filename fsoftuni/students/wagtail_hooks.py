from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.contrib.auth.models import Group
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.db.models import Q

from django.urls import include, path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.search import SearchArea
from wagtail.users.widgets import UserListingButton
from wagtail.admin.admin_url_finder import (
    ModelAdminURLFinder,
    register_admin_url_finder,
)
from wagtail.permission_policies import ModelPermissionPolicy


from .models import StudentProfile
from .page import StudentHomePage


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("student/", include("students.urls")),
    ]


add_user_perm = "{0}.add_{1}".format("students", "studentprofile".lower())
change_user_perm = "{0}.change_{1}".format("students", "studentprofile".lower())
delete_user_perm = "{0}.delete_{1}".format("students", "studentprofile".lower())


class StudentsMenuItem(MenuItem):
    def is_shown(self, request):
        return (
            request.user.has_perm(add_user_perm)
            or request.user.has_perm(change_user_perm)
            or request.user.has_perm(delete_user_perm)
        )


@hooks.register("register_admin_menu_item")
def register_students_menu_item():
    return StudentsMenuItem(
        _("Students"),
        reverse("students:index"),
        icon_name="doc-full-inverse",
        order=300,
    )


@hooks.register("register_permissions")
def register_student_permission():
    student_permission = Q(
        content_type__app_label="students",
        codename__in=[
            "add_%s" % "studentprofile",
            "change_%s" % "studentprofile",
            "delete_%s" % "studentprofile",
        ],
    )
    group_permissions = Q(
        content_type__app_label="auth",
        codename__in=["add_group", "change_group", "delete_group"],
    )

    return Permission.objects.filter(student_permission | group_permissions)


class StudentsSearchArea(SearchArea):
    def is_shown(self, request):
        return (
            request.user.has_perm(add_user_perm)
            or request.user.has_perm(change_user_perm)
            or request.user.has_perm(delete_user_perm)
        )


@hooks.register("register_admin_search_area")
def register_students_search_area():
    return StudentsSearchArea(
        _("Students"),
        reverse("students:index"),
        name="students",
        icon_name="user",
        order=600,
    )


@hooks.register("register_user_listing_buttons")
def student_listing_buttons(context, user):
    print(context)
    yield UserListingButton(
        _("Edit"),
        reverse("students:edit", args=[user.pk]),
        attrs={"title": _("Edit this student")},
        priority=10,
    )


class StudentAdminURLFinder(ModelAdminURLFinder):
    edit_url_name = "students:edit"
    permission_policy = ModelPermissionPolicy(StudentProfile)


register_admin_url_finder(StudentProfile, StudentAdminURLFinder)


@hooks.register("before_serve_page")
def redirect_to_login(page, request, serve_args, serve_kwargs):
    print("REDIT")
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("student_login"))


@hooks.register("before_create_page")
def before_create_page(request, parent_page, page_class):
    # Use a custom create view for the AwesomePage model

    if not request.user.is_superuser:
        if page_class == StudentHomePage:
            user = request.user
            if StudentHomePage.objects.filter(institute=user.institute).count():
                page_class.is_creatable = False



@hooks.register("before_create_user")
def before_create_user(request):
    print("before_create_user")
    data = {}
    data["for_user"] = request.user
    if request.method == "POST":
        print("IS POST")
        print(request.POST.__dict__)
        user = request.user
        
        if user.institute:
            data["institute"] = user.institute.id
            if user.department:
                data["department"] = user.department.id
                
            print("INSTITUTEYES")
            if str(user.role) == "Faculty Member":
                print("IS FM")
                student_role = Group.objects.get(name="Student")
                data["role"] = student_role.id
                data["student_role"] = student_role.id
                

                print("IS ")
                return {"status_code": 200}

    return data

