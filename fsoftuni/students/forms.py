from wagtail.admin.forms.models import WagtailAdminModelForm
from wagtail.users.forms import UserEditForm, UserCreationForm
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from users.models import CustomUser
from institutes.models import Institute
from departments.models import BatchYear, Batch

# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm


class StudentLogin(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if str(user.role) == "Student":
            print("LOGIN!")


class StudentCreationForm(WagtailAdminModelForm, UserCreationForm):

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
            "last_name",
            "username",
            "email",
            "institute",
            "batch",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):

        super(StudentCreationForm, self).__init__(*args, **kwargs)

        print("_______")
        user = kwargs.get("for_user")

        print(kwargs)

        print(user)
        print("_______")
        self.fields["username"].label = "Student ID"
        self.fields["username"].help_text = ""
        self.fields["username"].widget.attrs["class"] = "student_id"

        student_role = Group.objects.get(name="Student")

        self.fields["groups"].required = False

        if not user.is_superuser:
            print("NO SUPER USER")
            self.initial = {
                "institute": user.institute.id,
                "department": user.department.id,
                "role": student_role,
                "group": student_role,
            }
            # instance.initial = self.initial

            self.fields["institute"].disabled = True
            self.fields["department"].disabled = True

            if str(user.role) == "Faculty Member":

                b = Batch.objects.filter(assigned_faculty_member=user)
                self.fields["batch"].queryset = b
                self.initial["batch"] = b.first()
            else:
                self.fields["batch"].queryset = BatchYear.objects.filter(
                    batch__department=user.department
                )
        else:
            self.fields["institute"].queryset = Institute.objects.all()

    def clean(self):
        print("ORIGINAL CLEAN")
        if self.is_valid():
            username = self.cleaned_data["username"]
        print(self.is_valid())

    def clean_username(self):
        print("SECOND CLEAN")
        username = self.cleaned_data["username"]
        try:
            account = CustomUser.objects.exclude(pk=self.instance.pk).get(
                username=username
            )
            print("TRY")
        except CustomUser.DoesNotExist:
            print(" NOT EXIST")
            return username
        raise forms.ValidationError('Username "%s" is already in use.' % username)

    def _clean_username(self):
        print("CLEAAAN")
        username_field = CustomUser.USERNAME_FIELD
        # This method is called even if username if empty, contrary to clean_*
        # methods, so we have to check again here that data is defined.
        if username_field not in self.cleaned_data:
            return
        username = self.cleaned_data[username_field]

        users = CustomUser._default_manager.all()
        if self.instance.pk is not None:
            users = users.exclude(pk=self.instance.pk)
            print("IF FIRST")
        if users.filter(**{username_field: username}).exists():
            print("ERROR HERE")
            self.add_error(
                CustomUser.USERNAME_FIELD,
                forms.ValidationError(
                    self.error_messages["duplicate_username"],
                    code="duplicate_username",
                ),
            )
        print(username)
        print("CLEAN")
        return username

    def save(self, commit=True):
        print("SAVEEEEE")
        print(self.__dict__)
        student = super(UserCreationForm, self).save(commit=False)
        print(student.__dict__)
        # student.institute = user.institute
        if commit:
            # CustomUser.objects.create()
            student.save()
            student_role = Group.objects.get(name="Student")
            student.role = student_role
            student.groups.set([student_role])
        return student


class StudentEditForm(WagtailAdminModelForm, UserEditForm):
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

    class Meta(UserEditForm.Meta):
        model = CustomUser
        fields = [
            "is_active",
            "first_name",
            "department",
            "is_superuser",
            "last_name",
            "username",
            "email",
            "institute",
            "batch",
        ]

    def __init__(self, *args, **kwargs):
        super(StudentEditForm, self).__init__(*args, **kwargs)
        user = kwargs.get("initial").get("for_user")
        self.fields["username"].label = "Student ID"
        self.fields["username"].help_text = ""
        self.fields["username"].widget.attrs["class"] = "student_id"

        if not user.is_superuser:
            self.fields["batch"].disabled = True
            self.fields["department"].disabled = True
            self.fields["institute"].disabled = True


# (a) - institute code
# (2022) - year is this one automatically generate?
# (01) - degree
# (02) - department
# (001) - suffix
