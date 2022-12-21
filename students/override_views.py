from django.contrib.auth import get_user_model, update_session_auth_hash
from django.template.response import TemplateResponse
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.vary import vary_on_headers
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.auth import any_permission_required, permission_required
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, redirect
from wagtail import hooks
from wagtail.log_actions import log
from wagtail.admin import messages
from django.contrib.auth.models import Group
from django.urls import reverse
from .forms import StudentCreationForm, StudentEditForm

User = get_user_model()


def get_users_filter_query(q, model_fields):
    conditions = Q()

    for term in q.split():
        if "username" in model_fields:
            conditions |= Q(username__icontains=term)

        if "first_name" in model_fields:
            conditions |= Q(first_name__icontains=term)

        if "last_name" in model_fields:
            conditions |= Q(last_name__icontains=term)

        if "email" in model_fields:
            conditions |= Q(email__icontains=term)
        
        if "department" in model_fields:
            conditions |= Q(department__name__contains=term)
        
        if "batch" in model_fields:
            conditions |= Q(batch__year__exact=term)

    return conditions


add_user_perm = "{0}.add_{1}".format("students", "studentprofile".lower())
change_user_perm = "{0}.change_{1}".format("students", "studentprofile".lower())
delete_user_perm = "{0}.delete_{1}".format("students", "studentprofile".lower())


def user_can_delete_user(current_user, user_to_delete):
    if not current_user.has_perm(delete_user_perm):
        return False

    if current_user == user_to_delete:
        # users may not delete themselves
        return False

    if user_to_delete.is_superuser and not current_user.is_superuser:
        # ordinary users may not delete superusers
        return False

    return True


def get_user_creation_form():
    form_setting = "WAGTAIL_USER_CREATION_FORM"
    return StudentCreationForm


def get_user_edit_form():
    form_setting = "WAGTAIL_USER_EDIT_FORM"
    return StudentEditForm


@any_permission_required(add_user_perm, change_user_perm, delete_user_perm)
@vary_on_headers("X-Requested-With")
def index(request, *args):

    q = None
    is_searching = False

    group = None
    group_filter = Q()
    if args:
        group = get_object_or_404(Group, id=args[0])
        group_filter = Q(groups=group) if args else Q()

    model_fields = [f.name for f in User._meta.get_fields()]

    if "q" in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search students"))
        if form.is_valid():
            q = form.cleaned_data["q"]
            is_searching = True
            conditions = get_users_filter_query(q, model_fields)

            users = User.objects.filter(group_filter & conditions)
    else:
        form = SearchForm(placeholder=_("Search students"))

    if not is_searching:
        users = User.objects.filter(group_filter)

    if "last_name" in model_fields and "first_name" in model_fields:
        users = users.order_by("last_name", "first_name")

    users = users.filter(role__name="Student")

    if not request.user.is_superuser:
        users = users.filter(institute=request.user.institute)
        if str(request.user.role) == "Faculty Member":
            users = users.filter(batch__assigned_faculty_member=request.user)

    if "ordering" in request.GET:
        ordering = request.GET["ordering"]

        if ordering == "username":
            users = users.order_by(User.USERNAME_FIELD)
    else:
        ordering = "name"

    paginator = Paginator(users.select_related("wagtail_userprofile"), per_page=20)
    users = paginator.get_page(request.GET.get("p"))

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return TemplateResponse(
            request,
            "wagtailusers/users/results.html",
            {
                "users": users,
                "is_searching": is_searching,
                "query_string": q,
                "ordering": ordering,
            },
        )
    else:
        return TemplateResponse(
            request,
            "wagtailusers/students/index.html",
            {
                "group": group,
                "search_form": form,
                "users": users,
                "is_searching": is_searching,
                "ordering": ordering,
                "query_string": q,
                "app_label": User._meta.app_label,
                "model_name": User._meta.model_name,
            },
        )


# @permission_required(add_user_perm)
# def create(request):

#     print(request)
#     if request.method == "POST":
#         user = request.user
#         post_data = request.POST.copy()
#         if not user.is_superuser:
#             post_data['institute'] = user.institute.id
#             post_data['department'] = user.department.id


#         form = StudentCreationForm(post_data, request.FILES, initial={'for_user':request.user})
#         print(form.errors)

#         if form.is_valid():
#             print("FORM IS VALID")

#             user = form.save(commit=False)
#             log(user, "wagtail.create")
#             messages.success(
#                 request,
#                 _("User '{0}' created.").format(user),
#                 buttons=[
#                     messages.button(
#                         reverse("students:edit", args=(user.pk,)), _("Edit")
#                     )
#                 ],
#             )

#             return redirect("students:index")
#         else:
#             messages.error(request, _("The user could not be created due to errors."))
#     else:

#         form = StudentCreationForm(request.POST or None, request.FILES or None, initial={'for_user':request.user})
#     return TemplateResponse(
#         request,
#         "wagtailusers/students/create.html",
#         {
#             "form": form,
#         },
#     )


@permission_required(add_user_perm)
def create(request):
    for fn in hooks.get_hooks("before_create_user"):
        result = fn(request)
        if hasattr(result, "status_code"):
            return result
    if request.method == "POST":

        form = StudentCreationForm(request.POST, request.FILES, for_user=request.user)
        if form.is_valid():
            with transaction.atomic():
                user = request.user
                student = form.save(commit=False)
                student.institute = user.institute
                student.department = user.department
                student.save()
                log(student, "wagtail.create")
            messages.success(
                request,
                _("User '{0}' created.").format(student),
                buttons=[
                    messages.button(
                        reverse("students:edit", args=(student.pk,)), _("Edit")
                    )
                ],
            )
            for fn in hooks.get_hooks("after_create_user"):
                result = fn(request, student)
                if hasattr(result, "status_code"):
                    return result
            return redirect("students:index")
        else:
            messages.error(request, _("The user could not be created due to errors."))
    else:
        form = StudentCreationForm(
            request.POST or None, request.FILES or None, for_user=request.user
        )

    return TemplateResponse(
        request,
        "wagtailusers/students/create.html",
        {
            "form": form,
        },
    )


@permission_required(change_user_perm)
def edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    can_delete = user_can_delete_user(request.user, user)
    editing_self = request.user == user

    for fn in hooks.get_hooks("before_edit_user"):
        result = fn(request, user)
        if hasattr(result, "status_code"):
            return result
    if request.method == "POST":
        form = get_user_edit_form()(
            request.POST,
            request.FILES,
            instance=user,
            editing_self=editing_self,
            initial={"for_user": request.user},
        )
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                log(user, "wagtail.edit")

            if user == request.user and "password1" in form.changed_data:
                # User is changing their own password; need to update their session hash
                update_session_auth_hash(request, user)

            messages.success(
                request,
                _("User '{0}' updated.").format(user),
                buttons=[
                    messages.button(
                        reverse("students:edit", args=(user.pk,)), _("Edit")
                    )
                ],
            )
            for fn in hooks.get_hooks("after_edit_user"):
                result = fn(request, user)
                if hasattr(result, "status_code"):
                    return result
            return redirect("students:index")
        else:
            messages.error(request, _("The user could not be saved due to errors."))
    else:
        form = get_user_edit_form()(
            instance=user, editing_self=editing_self, initial={"for_user": request.user}
        )

    return TemplateResponse(
        request,
        "wagtailusers/students/edit.html",
        {
            "user": user,
            "form": form,
            "can_delete": can_delete,
        },
    )
