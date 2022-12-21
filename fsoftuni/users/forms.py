from django import forms
from django.conf import settings

from django.utils.translation import gettext_lazy as _

from wagtail.users.forms import UserEditForm, UserCreationForm

from wagtail.users.forms import GroupForm as WagtailGroupForm
from wagtail.admin.forms.models import WagtailAdminModelForm

from django.contrib.auth.models import Group
from .models import CustomGroup, CustomUser
from departments.models import Department
from institutes.models import Institute

# The standard fields each user model is expected to have, as a minimum.
standard_fields = {"email", "first_name", "last_name", "is_superuser", "groups"}
# Custom fields
if hasattr(settings, "WAGTAIL_USER_CUSTOM_FIELDS"):
    custom_fields = set(settings.WAGTAIL_USER_CUSTOM_FIELDS)
else:
    custom_fields = set()


class CustomUserEditForm(WagtailAdminModelForm, UserEditForm):
    class Meta(UserEditForm.Meta):
        model = CustomUser
        fields = [
            "is_active",
            "first_name",
            "department",
            "groups",
            "is_superuser",
            "last_name",
            "username",
            "email",
            "institute",
            "suffix",
            "role",
        ]

    def __init__(self, *args, **kwargs):
        super(CustomUserEditForm, self).__init__(*args, **kwargs)
        
        user = kwargs.get("initial").get("for_user")
        self.for_user = user
        instance = kwargs.pop("instance")

        institute = instance.institute
        departments = Department.objects.filter(institute=institute)
        
        self.fields["suffix"].label = "Section Code"
        self.fields["department"].queryset = departments

        self.fields["username"].help_text = ""
        self.fields["username"].label = "User ID"
        self.fields["username"].widget.attrs["readonly"] = True
        self.fields["username"].help_text = ""

        if str(instance.role) == 'Controller of Exam' or str(instance.role) == 'Proof Reader of Exam':
            self.fields['department'].disabled = True
            self.fields['department'].required = False


        if not user.is_superuser:
            self.fields["institute"].disabled = True

        if self.instance.is_superuser and kwargs.get("editing_self"):
            self.fields["department"].widget = forms.HiddenInput()
            self.fields["institute"].widget = forms.HiddenInput()
            self.fields["department"].label = ""
            self.fields["institute"].label = ""
            self.fields["department"].required = False
            self.fields["institute"].required = False
            self.fields["suffix"].required = False

    def save(self, commit=True):
        instance = super().save()
        instance.groups.set([instance.role])
        return instance


class CustomUserCreationForm(WagtailAdminModelForm, UserCreationForm):
    password1 = forms.CharField(
        label=_("Password"),
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Password",
                "style": "margin-bottom:2rem;margin-top:2rem;",
            }
        ),
        help_text=_("Leave blank if not changing."),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Password confirmation",
            }
        ),
        help_text=_("Enter the same password as above, for verification."),
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = [
            "is_active",
            "first_name",
            "department",
            "groups",
            "is_superuser",
            "last_name",
            "username",
            "email",
            "institute",
            "suffix",
            "role",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('for_user')
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)

        self.fields["suffix"].label = "Section Code"
        self.fields["username"].label = "User ID"
        self.fields["username"].widget.attrs["readonly"] = True
        self.fields["username"].help_text = ""
        self.fields["groups"].required = False
        self.fields['department'].required = False

        if not user.is_superuser:
            self.fields['institute'].queryset = Institute.objects.filter(id=user.institute.id)
            self.fields["institute"].initial = user.institute
            self.fields['institute'].disabled = True

    def save(self, commit=True):
        instance = super().save()

        if str(instance.role) == 'Controller of Exam' or str(instance.role) == 'Proof Reader of Exam' or str(instance.role) == 'Institute Head':
            instance.department = None

        return instance

    def clean(self):
        if str(self.cleaned_data['role']) == 'Controller of Exam' or str(self.cleaned_data['role']) == 'Proof Reader of Exam' or str(self.cleaned_data['role']) == 'Institute Head':
            self.fields['department'].required = False
            self.cleaned_data['department'] = None
            print("CLEAN")
        else:
            self.fields['department'].required = True

        cleaned_data = super(CustomUserCreationForm, self).clean()
        
        
        return cleaned_data

valid_group_names = ["Super User", "Department Head", "Institute Head", "Faculty Member", "Student", "Controller of Exam", "Proof Reader of Exam"]
class GroupForm(WagtailGroupForm):
    custom_group = forms.MultipleChoiceField(
        label="Can create role",
        required=False,
        choices=[],
    )
    name = forms.ChoiceField()

    def __init__(self, initial=None, instance=None, **kwargs):
        super(GroupForm, self).__init__(initial=initial, instance=instance, **kwargs)
        
        existing_role = list(set(Group.objects.all().values_list("name", flat=True)))
        valid_role = valid_group_names

        for role in existing_role:
            if role in valid_role:
                valid_role.remove(role)
        
        self.fields['name'].choices = [(role,role) for role in valid_role]
        self.fields['custom_group'].widget = forms.CheckboxSelectMultiple()
 
        if instance is not None and len(str(instance)):
            print("OIF")
            self.fields['name'].choices = [(instance.name, instance.name)]
            self.fields["custom_group"].choices = [
                (choice.pk, choice)
                for choice in Group.objects.exclude(name="Super User").exclude(
                    name=instance.name
                )
            ]
            self.fields["name"].initial = instance.name

            cg = CustomGroup.objects.filter(role=instance).first()

            if cg:
                i = [(item.pk) for item in cg.roles.all()]
                self.fields["custom_group"].initial = i

            if instance.name in valid_group_names:
                self.fields["name"].widget.attrs["readonly"] = True

        else:
            groups = Group.objects.exclude(name="Super User")
            if groups:
                self.fields["custom_group"].choices = [
                    (choice.pk, choice)
                    for choice in groups
                ]

    def save(self, commit=True):
        print("SAV!!!")
        instance = super().save()
        print(instance)
        print(instance.__class__)
        print(self.cleaned_data)
        if self.cleaned_data["custom_group"]:
            print(self.cleaned_data["custom_group"])
            cg, created = CustomGroup.objects.get_or_create(role=instance)
            print("CG")
            print(cg)
            if cg:
                cg.roles.set(self.cleaned_data["custom_group"])
            else:
                cg = CustomGroup.objects.create(role=instance)
                cg.roles.set(self.cleaned_data["custom_group"])
            # instance.custom_group.set(self.cleaned_data["custom_group"])

        return instance
