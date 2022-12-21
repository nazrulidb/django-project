from .models import Department, Batch, BatchYear
from django import forms
from wagtail.admin.forms.models import WagtailAdminModelForm
from institutes.models import Degree

from django.contrib.auth import get_user_model

Users = get_user_model()


class CustomBatchForm(WagtailAdminModelForm):
    class Meta:
        model = Batch
        fields = [
            "department",
            "name",
            "year",
            "suffix",
            "assigned_faculty_member",
            "degree",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        user = kwargs.pop("for_user")
        self.for_user = user
        instance = kwargs.pop("instance")


        print(kwargs)

        if not user.is_superuser:
            if str(user.role) == "Institute Head":
                self.fields["department"].queryset = Department.objects.filter(
                    institute=self.for_user.institute
                )
                self.fields["assigned_faculty_member"].queryset = Users.objects.filter(
                    institute=self.for_user.institute, role__name="Faculty Member"
                )
            elif str(user.role) == "Department Head":
                department = Department.objects.get(id=self.for_user.department.id)
                self.fields["department"].choices = [(department.id, department.name)]
                self.fields["assigned_faculty_member"].queryset = Users.objects.filter(
                    department=self.for_user.department, role__name="Faculty Member"
                )
            self.fields["degree"].queryset = Degree.objects.filter(institute=self.for_user.institute)
            
            if (
                not str(user.role) == "Institute Head"
                and not str(user.role) == "Department Head"
            ):

                self.fields["name"].disabled = True
                self.fields["assigned_faculty_member"].disabled = True
                self.fields["degree"].disabled = True
                if isinstance(instance, Batch):
                    del self.fields["department"]
                del self.fields["name"]
                del self.fields["assigned_faculty_member"]
                del self.fields["degree"]
                del self.fields["suffix"]

                # if str(user.role) == "Faculty Member":

    def clean(self):
        print("ORIGINAL CLEAN")
        department = self.cleaned_data["department"]
        assigned = self.cleaned_data["assigned_faculty_member"]

        if assigned and assigned.department != department:
            raise forms.ValidationError('department mismatch')
        
    # def save(self, commit=True):
    #     print("SAVE HERE")
    #     print(self.__dict__)
    #     print(self.formsets.get('students_batch'))
    #     instance = super().save()
    #     print("_____")
    #     return instance


class CustomBatchFormSet(WagtailAdminModelForm):
    class Meta:
        model = Batch
        fields = ["name", "suffix", "assigned_faculty_member", "degree"]

    def clean(self):
        print("ORIGINAL CLEAN")
        department = self.cleaned_data["department"]
        assigned = self.cleaned_data["assigned_faculty_member"]

        if assigned and assigned.department != department:
            raise forms.ValidationError('department mismatch')
            
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        user = kwargs.get("for_user")
        instance = kwargs.get("instance")

        if not user.is_superuser:

            try:
                institute = instance.department.institute
            except Exception as e:
                print(e)
                institute = user.institute
                if not institute and instance:
                    institute = instance.department.institute

            qset = Degree.objects.filter(institute=institute)
            self.fields["degree"].queryset = qset
            self.fields["assigned_faculty_member"].limit_choices_to = {
                "institute": institute
            }
            if (
                str(user.role) == "Institute Head"
                or str(user.role) == "Department Head"
            ):
                if isinstance(instance, Batch):
                    self.fields["department"].queryset = Department.objects.filter(
                        institute=institute
                    )
            else:
                self.fields["name"].disabled = True
                self.fields["assigned_faculty_member"].disabled = True
                self.fields["degree"].disabled = True

                del self.fields["department"]
                del self.fields["name"]
                del self.fields["assigned_faculty_member"]
                del self.fields["degree"]
                del self.fields["suffix"]

class BatchYearCreate(WagtailAdminModelForm):
    class Meta:
        model = BatchYear
        fields = [
            "batch",
            "level",
            "term",
            "year_to",
            "assigned_faculty_member",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        user = kwargs.get("for_user")

        if user.is_superuser:
            del self.fields["assigned_faculty_member"]
        else:
        
            self.fields["batch"].queryset = Batch.objects.filter(
                 department__institute__id =user.institute.id
            )

            self.fields["assigned_faculty_member"].queryset = Users.objects.filter(
                institute=user.institute, role__name="Faculty Member"
            )

class BatchYearEdit(WagtailAdminModelForm):
    class Meta:
        model = BatchYear
        fields = [
            "assigned_faculty_member",
        ]
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        
        self.fields["assigned_faculty_member"].queryset = Users.objects.filter(institute=instance.batch.department.institute, role__name="Faculty Member")



class DeptCreateForm(WagtailAdminModelForm):
    class Meta:
        model = Department
        fields = ("institute", "name", "alternative_name", "code")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.for_user = kwargs.get("for_user")

        print("DEPT FORM!")

        if not self.for_user.is_superuser:
            print("IF MGA DIM ")
            self.initial = {"institute": self.for_user.institute}
            self.fields["institute"].disabled = True
            

    def save(self, commit=True):
        instance = super().save()
        if self.for_user.institute:
            instance.institute = self.for_user.institute
        return instance


class DeptEditForm(WagtailAdminModelForm):
    class Meta:
        model = Department
        fields = ("name", "alternative_name", "code")

    def save(self, commit=True):
        instance = super().save()
        if self.for_user.institute:
            instance.institute = self.for_user.institute
        return instance

    # def save(self, commit=True):
    #     print("SAVE HERE")
    #     print(self.__dict__)
    #     print(self.formsets.get('students_batch'))
    #     instance = super().save()
    #     if self.for_user.is_superuser:
    #         instance.institute = self.for_user.institute
    #     print("_____")
    #     return instance
