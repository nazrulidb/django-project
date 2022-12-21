from django.shortcuts import HttpResponse, redirect
from django.templatetags.static import static
from django.utils.html import format_html
from wagtail.contrib.modeladmin.views import EditView, CreateView
from wagtail.core import hooks
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
    ModelAdminGroup,
)
from wagtail.contrib.modeladmin.views import IndexView
from wagtail.admin.edit_handlers import (
    FieldPanel,
    ObjectList,
)

from .models import Institute, Degree  # , CustomDocument
from .forms import DegreeForm


@hooks.register("insert_editor_css", order=100)
def editor_css():

    return format_html(
        '<link rel="stylesheet" href="{}">', static("base/css/custom.css")
    )


class InstituteView(IndexView):
    def dispatch(self, request, *args, **kwargs):
        print(request.user.role)
        print(request.user.groups.all())

        if request.user.role and request.user.role.name == "Institute Head":
            institute = request.user.institute
            print("SHOULD REDIRECT")
            if institute:
                return redirect(self.url_helper.get_action_url("edit", institute.id))

        return super().dispatch(request)


class InstituteAdmin(ModelAdmin):

    model = Institute
    menu_label = "Institutes"
    # menu_icon = 'fa-calendar-check-o'
    menu_order = 1
    add_to_admin_menu = False
    exclude_from_explorer = False
    add_to_settings_menu = False
    search_fields = "__str__"
    index_view_class = InstituteView

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only show people managed by the current user
        if not request.user.is_superuser:
            return qs.filter(id=request.user.institute.id)

        return qs

    def edit_view(self, request, instance_pk):

        if not request.user.is_superuser:
            self.edit_handler = ObjectList(
                [
                    FieldPanel("name"),
                    FieldPanel("code"),
                ]
            )

        kwargs = {"model_admin": self, "instance_pk": instance_pk}
        view_class = self.edit_view_class
        return view_class.as_view(**kwargs)(request)


class DegreeCreateView(CreateView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.request_user = request.user

    def get_form_class(self):
        return DegreeForm


class DegreeEditView(EditView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.request_user = request.user

    def get_form_class(self):
        return DegreeForm


class DegreeAdmin(ModelAdmin):

    model = Degree
    menu_label = "Degrees"

    menu_order = 2
    exclude_from_explorer = False
    add_to_settings_menu = False
    search_fields = "__str__"
    create_view_class = DegreeCreateView
    edit_view_class = DegreeEditView

    def get_list_display(self, request):
        if request.user.is_superuser:
            self.list_display = ("institute", "name", "code")
            return self.list_display
        else:
            self.list_display = ("name", "code")
            return self.list_display

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only show people managed by the current user
        if not request.user.is_superuser:
            return qs.filter(institute=request.user.institute)
        return qs


class InstituteGroup(ModelAdminGroup):
    menu_label = "Institute"
    menu_icon = "folder-open-inverse"
    menu_order = 2
    items = (InstituteAdmin, DegreeAdmin)


modeladmin_register(InstituteGroup)


# class MyPermissionHelper(PermissionHelper):
#     def user_can_delete_obj(self, user, obj):
#         print("USER CAN DELETE")
#         if user:
#             return False

#         perm_codename = self.get_perm_codename("delete")
#         return self.user_has_specific_permission(user, perm_codename)

# class CustomDocumentDeleteView(DeleteView):
#     def dispatch(self, request, *args, **kwargs):
#         print("DISPATCH!!!")
#         if not self.check_action_permitted(request.user):
#             raise PermissionDenied
#         if self.is_pagemodel:
#             return redirect(self.url_helper.get_action_url("delete", self.pk_quoted))
#         return super().dispatch(request, *args, **kwargs)

#     def delete_instance(self):
#         return False

# class CustomDocumentAdmin(ModelAdmin):
#     model = CustomDocument
#     menu_label = 'Docs'
#     delete_view_class = CustomDocumentDeleteView
#     permission_helper_class = MyPermissionHelper
#     exclude_from_explorer = True
#     index_template_name = 'wagtaildocs/documents/index.html'
#     create_template_name = 'wagtaildocs/documents/add.html'
#     edit_template_name = 'wagtaildocs/documents/edit.html'

# modeladmin_register(CustomDocumentAdmin)

@hooks.register("describe_collection_contents")
def describe_docs(collection):
    print('describe_collection_docs')
    print(collection)

@hooks.register('construct_snippet_action_menu')
def remove_delete_option(menu_items, request, context):
    print('construct_snippet_action_menu')
    print(menu_items)
    # menu_items[:] = [item for item in menu_items if item.name != 'delete']



@hooks.register('before_create_snippet')
def snipper_create(request, instance):
    print('before_create_snippet')
    print(instance)
    

@hooks.register("construct_document_chooser_queryset")
def filter_document_queryset(documents, request):
    # Only show uploaded documents
    print('construct_document_chooser_queryset')
    if not request.user.is_superuser:
        documents = documents.filter(institute=request.user.institute)

    return documents

@hooks.register("construct_explorer_page_queryset")
def filter_by_institute2(parent_page, pages, request):
    print("construct_explorer_page_queryset")
    print(parent_page)
    print(pages)
    if not request.user.is_superuser:
        pages = pages.filter(studenthomepage__institute=request.user.institute)
    print(pages)
    return pages


@hooks.register("construct_page_chooser_queryset")
def filter_by_institute3(pages, request):
    # Only show own pages
    if not request.user.is_superuser:
        pages = pages.filter(studenthomepage__institute=request.user.institute)

    return pages

# @hooks.register("construct_image_chooser_queryset")
# def filter_by_institute4(images, request):
#     # Only show uploaded images
#     if not request.user.is_superuser:
#         images = images.filter(institute=request.user.institute)

#     return images

@hooks.register('after_create_snippet')
def after_create_snippet(request, instance):
    print('after_create_snippet')
    print(instance)

@hooks.register("before_delete_snippet")
def before_snippet_delete(request, instances):
    # "instances" is a QuerySet
    print("BEFORE EDIT SNIPPET!!!!")
    total = len(instances)

    if request.method == "POST":
        # Override the deletion behaviour
        instances.delete()

        return HttpResponse(
            f"{total} snippets have been deleted", content_type="text/plain"
        )
