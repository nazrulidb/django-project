from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = CustomUser
    list_display = ["pk", "email", "username", "first_name", "last_name"]
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "groups",
                    "institute",
                    "department",
                )
            },
        ),
    )
    fieldsets = UserAdmin.fieldsets + (
        (
            None,
            {
                "fields": (
                    "institute",
                    "department",
                    "metadata",
                )
            },
        ),
    )

    def get_queryset(self, request):
        print("user get_queryset")
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(author=request.user)


admin.site.register(CustomUser, CustomUserAdmin)
