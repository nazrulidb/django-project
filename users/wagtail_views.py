from django.template.response import TemplateResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.vary import vary_on_headers
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.auth import any_permission_required, permission_required
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.urls import reverse
from wagtail import hooks
from wagtail.log_actions import log
from wagtail.admin import messages
from .forms import CustomUserEditForm, CustomUserCreationForm

from users.models import *

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

    return conditions


add_user_perm = "{0}.add_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
change_user_perm = "{0}.change_{1}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)
delete_user_perm = "{0}.delete_{1}".format(
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower()
)
# add_user_perm = "{0}.add_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME)
# change_user_perm = "{0}.change_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME)
# delete_user_perm = "{0}.delete_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME)

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
        form = SearchForm(request.GET, placeholder=_("Search users"))
        if form.is_valid():
            q = form.cleaned_data["q"]
            is_searching = True
            conditions = get_users_filter_query(q, model_fields)

            users = User.objects.filter(group_filter & conditions)
    else:
        form = SearchForm(placeholder=_("Search users"))

    if not is_searching:
        users = User.objects.filter(group_filter)

    if "last_name" in model_fields and "first_name" in model_fields:
        users = users.order_by("last_name", "first_name")

    users = users.exclude(role__name="Student")

    if not request.user.is_superuser:
        print(f'user role {request.user.role}')
        custom_group = CustomGroup.objects.filter(role=request.user.role).first()
        group_qset = custom_group.roles.all()
        users = users.filter(role__in=group_qset)

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
            "wagtailusers/users/index.html",
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

    return conditions





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


def get_user_edit_form():
    form_setting = "WAGTAIL_USER_EDIT_FORM"
    return CustomUserEditForm

@permission_required(change_user_perm)
def edit(request, user_id):
    print("EDIT!!!")
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
                        reverse("wagtailusers_users:edit", args=(user.pk,)), _("Edit")
                    )
                ],
            )
            for fn in hooks.get_hooks("after_edit_user"):
                result = fn(request, user)
                if hasattr(result, "status_code"):
                    return result
            return redirect("wagtailusers_users:index")
        else:
            messages.error(request, _("The user could not be saved due to errors."))
    else:
        form = get_user_edit_form()(
            instance=user, editing_self=editing_self, initial={"for_user": request.user}
        )

    return TemplateResponse(
        request,
        "wagtailusers/users/edit.html",
        {
            "user": user,
            "form": form,
            "can_delete": can_delete,
        },
    )


@permission_required(add_user_perm)
def create(request):
    for fn in hooks.get_hooks("before_create_user"):
        result = fn(request)
        if hasattr(result, "status_code"):
            return result
    if request.method == "POST":

        form = CustomUserCreationForm(request.POST, request.FILES, for_user=request.user)
        if form.is_valid():
            with transaction.atomic():
                
                user = form.save(commit=False)
                user.save()
                log(user, "wagtail.create")
            messages.success(
                request,
                _("User '{0}' created.").format(user),
                buttons=[
                    messages.button(
                        reverse("wagtailusers_users:edit", args=(user.pk,)), _("Edit")
                    )
                ],
            )
            for fn in hooks.get_hooks("after_create_user"):
                result = fn(request, user)
                if hasattr(result, "status_code"):
                    return result
            return redirect("wagtailusers_users:index")
        else:
            messages.error(request, _("The user could not be created due to errors."))
    else:
        form = CustomUserCreationForm(
            request.POST or None, request.FILES or None, for_user=request.user
        )

    return TemplateResponse(
        request,
        "wagtailusers/users/create.html",
        {
            "form": form,
        },
    )