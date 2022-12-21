from django.db.models import Q
from django.utils.html import mark_safe
from django import forms
from django.core.files.base import ContentFile
from django.contrib.admin import SimpleListFilter

from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtail.contrib.modeladmin.views import InspectView, IndexView, EditView, CreateView
from wagtail.search.utils import AND, OR
from wagtail.contrib.modeladmin.helpers import PermissionHelper

from wagtail.core.models import Collection
from wagtail.admin.edit_handlers import (
    FieldPanel,
    ObjectList
)

from students.models import StudentRecord
from institutes.models import CustomDocument
from departments.models import Batch

from .models import StudentRecords, BatchUploadResult
from .forms import StudentRecordsForm, StudentRecordsEditForm, CertGenForm


class CustomIndexView(IndexView):
    def dispatch(self, request, *args, **kwargs):
        index_url = self.url_helper.get_action_url("index")
        create_url = self.url_helper.get_action_url("create")
        self.index_url = index_url
        self.create_url = create_url
        if not request.GET.get("status__exact"):
            self.tab1 = "true"
        else:
            self.tab2 = "true"

        return super().dispatch(request, *args, **kwargs)


class RecordsCreateView(CreateView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.request_user = request.user

    def get_form_class(self):
        return StudentRecordsForm
    

class RecordsEdit(EditView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        doc_data = context["instance"].link_document.get_data()
        s = self.request.GET.get("sheet")

        if s and doc_data.get("excel_data").get(s):
            current_sheet = s.upper()
            sheet = doc_data.get("excel_data").get(current_sheet)
        else:
            try:
                current_sheet = next(iter(doc_data.get("excel_data")))
                sheet = doc_data.get("excel_data").get(current_sheet)
            except Exception as e:
                print(e)
                current_sheet = None
                sheet = None
        try:
            headers = next(iter(sheet)).keys()
        except Exception as e:
            print(e)
            headers = None

        context["dt"] = {
            "data": sheet,
            "headers": headers,
            "sheets": doc_data.get("sheets"),
            "current_sheet": current_sheet,
        }

        return context

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.request_user = request.user
        print(request)
        print(args)
        print(kwargs)
        # pp(self.__dict__)

    def get_form_class(self):
        return StudentRecordsEditForm


# class MyButtonHelper(ButtonHelper):
#     def get_buttons_for_obj(
#         self, obj, exclude=None, classnames_add=None, classnames_exclude=None
#     ):
#         print("GET BUTTOn")
#         inspect(self.view)
#         if exclude is None:
#             exclude = []
#         if classnames_add is None:
#             classnames_add = []
#         if classnames_exclude is None:
#             classnames_exclude = []
#         ph = self.view.permission_helper
#         usr = self.request.user
#         pk = getattr(obj, self.opts.pk.attname)
#         btns = []
#         if "inspect" not in exclude and ph.user_can_inspect_obj(usr, obj):
#             btns.append(self.inspect_button(pk, classnames_add, classnames_exclude))
#         if "edit" not in exclude and ph.user_can_edit_obj(usr, obj):
#             print(ph.user_can_edit_obj(usr, obj))
#             print("CAN EDIT")
#             btns.append(self.edit_button(pk, classnames_add, classnames_exclude))
#         if "delete" not in exclude and ph.user_can_delete_obj(usr, obj):
#             btns.append(self.delete_button(pk, classnames_add, classnames_exclude))
#         return btns


class MyPermissionHelper(PermissionHelper):
    def user_can_edit_obj(self, user, obj):
        perm_codename = self.get_perm_codename("change")

        if str(user.role) == "Controller of Exam":
            if obj.status == "pending" or obj.status == "processing" or obj.publish:
                return False
            return True

        elif str(user.role) == "Proof Reader of Exam":
            if obj.status == "approve":
                return False
            return True

        else:
            return self.user_has_specific_permission(user, perm_codename)

    def user_can_delete_obj(self, user, obj):
        if str(user.role) == "Controller of Exam":
            if obj.status == "processing" and obj.extract_timeout():
                return True
            if obj.status == "invalid" or obj.status == "pending":
                return True
        elif user.is_superuser:
            return True

        return False



class StudentRecordsAdmin(ModelAdmin):
    model = StudentRecords
    menu_label = "Batch Upload"
    menu_icon = 'folder-open-inverse'
    menu_order = 1
    exclude_from_explorer = False
    add_to_settings_menu = False

    list_filter = ("status",)
    list_select_related = [
        "institute",
        "link_document",
        "assigned_pr",
        "assigned_controller"
    ]
    search_fields = ("created_at", "name", "comment", "approve_at", "Status")
    extra_search_kwargs = {"operator": OR, "status": AND}
    permission_helper_class = MyPermissionHelper
    # button_helper_class = MyButtonHelper

    index_template_name = "modeladmin/student_records/index.html"
    create_template_name = "modeladmin/student_records/create.html"
    edit_template_name = "modeladmin/student_records/edit.html"

    index_view_class = CustomIndexView
    create_view_class = RecordsCreateView
    edit_view_class = RecordsEdit
    list_display_add_buttons = (None,)
        
    def Status(self, obj):
        if obj.status == "approve" and obj.publish:
            return f"approve(published)"
        
        else:
            return obj.status

    def assigned_controller(self, obj):
        return str(obj.assigned_controller)

    def assigned(self, obj):
        if obj.assigned_pr == self.request_user:
            return "You"
        else:
            return obj.assigned_pr

    def get_extra_attrs_for_field_col(self, obj, field_name=None):
        attrs = super().get_extra_attrs_for_field_col(obj, field_name)

        if (
            str(self.request_user.role) == "Controller of Exam"
            and field_name == "assigned_controller"
            and obj.status == "pending"
        ):
            attrs.update(
                {
                    "disable-edit": "true",
                }
            )

        elif (
            str(self.request_user.role) == "Proof Reader of Exam"
            and field_name == "assigned_controller"
            and obj.status == "approve"
        ):
            attrs.update(
                {
                    "disable-edit": "true",
                }
            )
        elif self.request_user.is_superuser:
            attrs.update(
                {
                    "disable-edit": "false",
                }
            )

        return attrs

    # def get_extra_attrs_for_row(self, obj, context):
    #     print(obj)
    #     print(context)

    def action(self, obj):

        if str(self.request_user.role) == "Proof Reader of Exam":
            if obj.status != "approve":
                return mark_safe(
                    f'<a class="abtn button button-small button-secondary" href="/cms/custom_dashboard/studentrecords/edit/{obj.id}/">Edit</a>'
                )
            else:
                return ""
        else:
            if self.request_user.is_superuser:
                return mark_safe(
                    f'<a class="abtn button no button-small button-secondary" href="/cms/custom_dashboard/studentrecords/delete/{obj.id}/">REMOVE</a>'
                )
            else:
                if obj.status == "approve" and not obj.publish:
                    return mark_safe(
                        """<a class="abtn button button-small button-secondary" href="/batch_records/publish/{}">Generate</a> \
                                """.format(str(obj.id))
                    )
                elif obj.status == "processing":
                    if obj.extract_timeout():
                        return mark_safe(
                            f'<a class="abtn button no button-small button-secondary" href="/cms/custom_dashboard/studentrecords/delete/{obj.id}/">REMOVE</a>'
                        )
                    return ""
                elif obj.status == "invalid":
                    return mark_safe(
                        f'<a class="abtn button no button-small button-secondary" href="/cms/custom_dashboard/studentrecords/delete/{obj.id}/">REMOVE</a>'
                    )
                else:
                    return mark_safe(
                        """<a class="abtn button no button-small button-secondary" href="/batch_records/publish/{}">Unpublish</a> \
                        """.format(str(obj.id))
                    )

    def remarks(self, obj):
        r = obj.link_document.get_data().get('student_records')
        if r:
            sr = r.get("student_record_saved")
            m = f'{r.get("match")}/{r.get("total")} <br> saved records: None'
            if len(sr):
                sr = ', '.join(sr)
                m = f'{r.get("match")}/{r.get("total")} <br> saved records: {sr}'
            
            return mark_safe(m)

    def get_list_display(self, request):
        if request.user.is_superuser:
            self.list_display = (
                "name",
                "level",
                "term",
                "year",
                "institute",
                "assigned_controller",
                "assigned_pr",
                "created_at",
                "Status",
                "remarks",
                "action",
            )

        elif str(request.user.role) == "Controller of Exam":
            if request.GET.urlencode() == "status__exact=pending":
                self.list_display = (
                    "name",
                    "level",
                    "term",
                    "year",
                    "assigned_controller",
                    "assigned_pr",
                    "created_at",
                    "Status",
                    "remarks",
                )
            else:
                self.list_display = (
                    "name",
                    "level",
                    "term",
                    "year",
                    "assigned_controller",
                    "assigned_pr",
                    "created_at",
                    "Status",
                    "remarks",
                    "action",
                )

        elif str(request.user.role) == "Proof Reader of Exam":
            self.list_display = (
                "name",
                "level",
                "term",
                "year",
                "assigned_controller",
                "assigned",
                "created_at",
                "Status",
                "remarks",
                "action",
            )

        return self.list_display

    def get_queryset(self, request):

        self.request_user = request.user
        qs = super().get_queryset(request)

        if (
            not request.GET.get("status__exact")
            and str(self.request_user.role) == "Controller of Exam"
        ):
            qs = qs.filter(~Q(status="pending"))

        if not request.user.is_superuser:
            return qs.filter(Q(institute=request.user.institute)).order_by(
                "-created_at"
            )
        else:
            return qs.order_by("institute")

  

    def create_view(self, request):
        self.request_user = request.user
        self.create_view = True
        kwargs = {"model_admin": self}
        view_class = self.create_view_class
        return view_class.as_view(**kwargs)(request)

    def edit_view(self, request, instance_pk):
        self.request_user = request.user
        self.create_view = False
        if str(self.request_user.role) == "Proof Reader of Exam":
            self.menu_label == "Result View"

        kwargs = {"model_admin": self, "instance_pk": instance_pk}
        view_class = self.edit_view_class
        return view_class.as_view(**kwargs)(request)



class CertEdit(EditView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.request_user = request.user

    def get_form_class(self):
        return CertGenForm
    
    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs.update({"instance": self.get_instance(), "for_user": self.request.user})
    #     print("get_form_kwargs")
    #     return kwargs
    

    def post(self, request, *args, **kargs):
        from main.views import cert
        from django.core.files import File
        from wagtail.admin.forms.collections import CollectionForm
        from wagtail.core.models import Collection
        form = self.get_form()
        print("POST !!!!!!!!")
        
        instance = self.instance
        
        
        parent = instance.batch_year.collection
        if parent and not instance.collection:
            name = f'{parent.name} - Files'
            existing_collection = Collection.objects.filter(name=name).first()
            print(f'existing_collection {existing_collection}')
            if not existing_collection:
                form = CollectionForm({'parent':parent.pk, 'name':name})
                
                if form.is_valid():
                    collection = form.save(commit=False)
                    parent.add_child(instance=collection)
                    collection.save()
                    instance.collection = collection
                    instance.save()
            else:
                instance.collection = existing_collection
                instance.save()

        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            students = instance.students.all()
            print(f'students {students}')
            students_id = list(students.values_list("id", flat=True))
            print(f'students_id {students_id}')
            student_records = StudentRecord.objects.filter(student__id__in=students_id, retake=False)
            print(f'student_records {student_records}')
            for record in student_records:
                data = record.get_data_for_provisional_cert()
                data['date'] = instance.date
                print(data)
                pdf_byte = cert(request, data=data)
                print(pdf_byte)
                fname = f'{data.get("full_name")}.pdf'
                pdf = ContentFile(pdf_byte.getvalue())
                print(pdf)
                # obj, created = CustomDocument.objects.get_or_create(
                #     institute=record.student.institute,
                #     title=data.get('full_name'),
                #     file=pdf,
                #     collection=instance.collection
                # )
                print(f'parent collection {parent}')
                print(f'instance.collection {instance.collection}')
                
                d = CustomDocument(
                    collection=instance.collection,
                    institute=record.student.institute,
                    title=data.get('full_name'))
                
                d.file.save(fname, pdf, save=False)
                d.save()
               
        
        context = self.get_context_data()
        print("CONTEXT")
        
        response = self.render_to_response(context)
        print("_)____________________")
        return response
        
class CertificatePermission(PermissionHelper):
    def user_can_edit_obj(self, user, obj):
        if obj.batch_file and obj.batch_file.publish:
            return True

        return False

    def user_can_create(self, user):
        return False

class CertificateGenerationAdmin(ModelAdmin):
    model = BatchUploadResult
    menu_label = "Certificate Generator"
    menu_icon = 'doc-full'
    menu_order = 2
    exclude_from_explorer = False
    add_to_settings_menu = False
    permission_helper_class = CertificatePermission
    edit_view_class = CertEdit


class BatchFilter(SimpleListFilter):
    title = "Batch"
    parameter_name = "batch"

    def lookups(self, request, model_admin):
        qset = Batch.objects.order_by('name').distinct('name')
        batches = set([c.student.batch for c in model_admin.model.objects.select_related('student').all()])
        print("LOOKUPS")

        print(batches)
        return [(c.id, c.name) for c in batches]


    def queryset(self, request, queryset):
        print("queryset")
        print()
        return queryset.all()

class MyPermissionHelper2(PermissionHelper):
    def user_can_create(self, user):
        return False
    def user_can_edit_obj(self, user, obj):
        return False
    def user_can_delete_obj(self, user, obj):
        return False

class StudentResultInspectView(InspectView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        instance = context["instance"]

        context['student_name'] = instance.student.full_name()
        context['student'] = instance.student

        return context

class StudentResultAdmin(ModelAdmin):
    model = StudentRecord
    menu_label = "Grade Sheet"
    menu_icon = 'form'
    menu_order = 3
    exclude_from_explorer = False
    add_to_settings_menu = False
    search_fields = ("student__first_name", "student__last_name", "student__username")
    list_filter = ("level", "term", "year")
    permission_helper_class = MyPermissionHelper2
    list_display_add_buttons = (None,)
    inspect_view_enabled = True
    inspect_template_name = "modeladmin/student_results/inspect.html"
    inspect_view_class = StudentResultInspectView

    def get_extra_attrs_for_field_col(self, obj, field_name=None):
        attrs = super().get_extra_attrs_for_field_col(obj, field_name)

        attrs.update(
                {
                    "disable-edit": "false",
                }
            )
        return attrs

    def get_queryset(self, request):
        self.request_user = request.user
        qs = super().get_queryset(request)

        return qs.filter(publish=True).order_by('student').distinct('student')

    def username(self, obj):
        return f"{obj.student.username}"

    def name(self, obj):
        
        return mark_safe(f'<a href="/cms/students/studentrecord/inspect/{obj.id}/" title="Inspect this Student Record">{obj.student.full_name()}</a>')

    def get_list_display(self, request):
        self.list_display = (
            'name',
            'username'
        )
        return self.list_display
        
class DashboardGroups(ModelAdminGroup):
    menu_label = "Dashboard"
    menu_icon = "home"
    menu_order = 2
    items = (StudentRecordsAdmin, CertificateGenerationAdmin, StudentResultAdmin)

modeladmin_register(DashboardGroups)

