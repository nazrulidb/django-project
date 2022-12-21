from django.shortcuts import redirect

from django.db.models import Q

from wagtail.admin import messages
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
    ModelAdminGroup,
)
from wagtail.contrib.modeladmin.views import IndexView, EditView, CreateView

from .models import Department, Batch, BatchYear

from .forms import DeptCreateForm, CustomBatchForm, DeptEditForm, BatchYearEdit, BatchYearCreate
from users.models import CustomUser
from students.forms import StudentCreationForm, StudentEditForm


class DepartmentView(IndexView):
    def dispatch(self, request, *args, **kwargs):

        if request.user.role and request.user.role.name == "Department Head":
            department = request.user.department

            if department:
                return redirect(self.url_helper.get_action_url("edit", department.id))

        return super().dispatch(request)


class DepartmentCreateView(CreateView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.request_user = request.user

    def get_form_class(self):
        return DeptCreateForm


class DepartmentEditView(EditView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.request_user = request.user

    def get_form_class(self):
        return DeptEditForm


class DepartmentAdmin(ModelAdmin):
    model = Department
    menu_label = "Departments"
    menu_icon = "user"
    menu_order = 2
    exclude_from_explorer = False
    add_to_settings_menu = False
    search_fields = "__str__"
    index_view_class = DepartmentView
    create_view_class = DepartmentCreateView
    edit_view_class = DepartmentEditView
    create_template_name = "modeladmin/departments/create.html"
    edit_template_name = "modeladmin/departments/edit.html"

    def get_queryset(self, request):
        print("GET QUERYSET")
        print(request.user.role)
        self.request_user = request.user
        qs = super().get_queryset(request)

        if not request.user.is_superuser:

            if request.user.role.name == "Institute Head":
                return qs.filter(institute=request.user.institute)

            elif request.user.role.name == "Department Head":
                return qs.filter(id=request.user.department.id)

            return qs.none()
        else:

            return qs.order_by("institute")

    def get_list_display(self, request):
        if request.user.is_superuser:
            self.list_display = ("institute", "name", "code")
            return self.list_display
        else:
            self.list_display = ("name", "code")
            return self.list_display

    def create_view(self, request):
        self.request_user = request.user
        self.create_view = True
        kwargs = {"model_admin": self}
        view_class = self.create_view_class
        return view_class.as_view(**kwargs)(request)

    def edit_view(self, request, instance_pk):
        self.request_user = request.user
        self.create_view = False
        kwargs = {"model_admin": self, "instance_pk": instance_pk}
        view_class = self.edit_view_class
        return view_class.as_view(**kwargs)(request)


class BatchCreate(CreateView):
    def get_form_class(self):
        return CustomBatchForm


class BatchEdit(EditView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.request_user = request.user
        kwargs.update({"is_edit": True})

    def get_form_class(self):
        return CustomBatchForm

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     print(kwargs)
    #     kwargs.update({"parent_instance": self.get_instance(), "for_user": self.request.user})
    #     return kwargs

    def form_invalid(self, form):

        messages.validation_error(self.request, self.get_error_message(), form)
        return self.render_to_response(self.get_context_data(form=form))


class BatchAdmin(ModelAdmin):
    model = Batch
    menu_label = "Batch"
    # menu_icon = 'fa-calendar-check-o'
    menu_order = 2
    exclude_from_explorer = False
    add_to_settings_menu = False
    search_fields = "__str__"
    list_display = ("Name", "year", "department", "degree", "assigned_faculty_member")

    create_view_class = BatchCreate
    edit_view_class = BatchEdit

    list_select_related = True

    
    def Name(self, obj):
        return f'{obj.name}-{obj.suffix}'

    def get_queryset(self, request):
        self.request_user = request.user
        qs = super().get_queryset(request)
        qs = qs.select_related("department", "degree")
        if request.user.is_superuser:
            return qs

        if request.user.role.name == "Institute Head":
            print("Institute Head")
            qs = qs.filter(Q(department__institute=request.user.institute))

        elif request.user.role.name == "Department Head":
            qs = qs.filter(Q(department=request.user.department))
            print("Department Head")

        elif request.user.role.name == "Faculty Member":
            qs = qs.filter(Q(assigned_faculty_member=request.user))
            print("Faculty Member")

        return qs

    def create_view(self, request):
        self.request_user = request.user
        self.is_edit = False
        kwargs = {"model_admin": self}
        view_class = self.create_view_class
        return view_class.as_view(**kwargs)(request)

    def edit_view(self, request, instance_pk):
        self.request_user = request.user
        self.is_edit = True
        kwargs = {"model_admin": self, "instance_pk": instance_pk}
        view_class = self.edit_view_class
        return view_class.as_view(**kwargs)(request)


class YearCreate(CreateView):
    def get_form_class(self):
        return BatchYearCreate


class YearEdit(EditView):
    def get_form_class(self):
        return BatchYearEdit

class BatchYearAdmin(ModelAdmin):
    model = BatchYear
    menu_label = "Class"
    # menu_icon = 'fa-calendar-check-o'
    menu_order = 3
    exclude_from_explorer = False
    add_to_settings_menu = False
    search_fields = "__str__"
    list_display = ("batch_name", "level", "term", "year", "assigned_faculty_member", "student_count")
    
    create_view_class = YearCreate
    edit_view_class = YearEdit
    list_filter = ("batch",)

    list_select_related = True

    def get_queryset(self, request):
        self.request_user = request.user
        qs = super().get_queryset(request)
        qs = qs.select_related("batch", "assigned_faculty_member")

        if request.user.is_superuser:
            return qs

        if request.user.role.name == "Institute Head":
            print("Institute Head")
            qs = qs.filter(Q(batch__department__institute=request.user.institute))

        elif request.user.role.name == "Department Head":
            qs = qs.filter(Q(batch__department=request.user.department))
            print("Department Head")

        elif request.user.role.name == "Faculty Member":
            qs = qs.filter(Q(assigned_faculty_member=request.user))
            print("Faculty Member")

        return qs

    
    def batch_name(self, obj):
        return obj.batch.name

    def year(self, obj):
        return obj.year_to

    def student_count(self, obj):
        return obj.students.all().count()

# class StudentCreateView(CreateView):
#     def get_form_class(self):
#         return StudentCreationForm

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         print(kwargs)
#         kwargs.update({"instance": self.get_instance(), "for_user": self.request.user})
#         return kwargs


# class StudentEditView(EditView):
#     def get_form_class(self):
#         return StudentEditForm

#     def setup(self, request, *args, **kwargs):
#         super().setup(request, *args, **kwargs)
#         self.request_user = request.user
#         kwargs.update({"is_edit": True})


# class StudentAdmin(ModelAdmin):
#     model = CustomUser
#     menu_label = "Students"
#     menu_icon = "user"
#     menu_order = 3
#     exclude_from_explorer = False
#     add_to_settings_menu = False
#     search_fields = ("first_name", "last_name", "username")
#     create_view_class = StudentCreateView
#     edit_view_class = StudentEditView
#     create_template_name = "wagtailusers/students/create.html"
#     edit_template_name = "wagtailusers/students/edit.html"
#     index_template_name = "wagtailusers/students/index.html"

#     def degree(self, obj):
#         if obj.batch:
#             return obj.batch.degree
#         else:
#             return ""

#     def name(self, obj):
#         return f"{obj.last_name} {obj.first_name}"

#     def get_list_display(self, request):
#         if request.user.is_superuser:
#             self.list_display = ("name", "institute", "department", "batch", "degree")
#             return self.list_display
#         else:
#             self.list_display = ("name", "batch", "degree")
#             return self.list_display

#     def get_queryset(self, request):
#         self.request_user = request.user
#         qs = super().get_queryset(request)

#         qs = qs.filter(Q(role__name="Student")).select_related(
#             "batch", "department", "institute"
#         )

#         if request.user.is_superuser:
#             return qs

#         if request.user.role.name == "Institute Head":
#             print("Institute Head")
#             qs = qs.filter(Q(institute=request.user.institute))

#         elif request.user.role.name == "Department Head":
#             qs = qs.filter(Q(department=request.user.department))
#             print("Department Head")

#         elif request.user.role.name == "Faculty Member":
#             qs = qs.filter(Q(batch__assigned_faculty_member=request.user))
#             print("Faculty Member")

#         return qs

#     def create_view(self, request):
#         self.request_user = request.user
#         self.is_edit = False
#         kwargs = {"model_admin": self}
#         view_class = self.create_view_class
#         return view_class.as_view(**kwargs)(request)

#     def edit_view(self, request, instance_pk):
#         self.request_user = request.user
#         self.is_edit = True
#         kwargs = {"model_admin": self, "instance_pk": instance_pk}
#         view_class = self.edit_view_class
#         return view_class.as_view(**kwargs)(request)


class DepartmentGroup(ModelAdminGroup):
    menu_label = "Department"
    menu_icon = "folder-open-inverse"
    menu_order = 3
    items = (DepartmentAdmin, BatchAdmin)


modeladmin_register(DepartmentGroup)
