from wagtail.core.models import Page
from wagtail.admin.edit_handlers import (
    FieldPanel,
    MultiFieldPanel,
)
from wagtail.core.fields import RichTextField
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from django.db import models
from django.utils.functional import classproperty
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import logout
from wagtail.admin.forms import WagtailAdminPageForm

from institutes.models import Institute


class StudentHomepageRoute(RoutablePageMixin, Page):
    # live = False

    @classproperty
    def is_creatable(cls):
        return not cls.objects.exists()

    @route(r"/^$")
    def serve(self, request, *args, **kwargs):
        if request.user.is_authenticated and str(request.user.role) != "Student":
            logout(request)

        print(request.user)
        context = self.get_context(request)
        if str(request.user.role) == "Student":
            home = StudentHomePage.objects.filter(
                institute=request.user.institute
            ).first()
            print(home.full_url)
            return HttpResponseRedirect(home.full_url)

    # is_previewable = False
    # def is_previewable(self):
    #     return False

    # parent_page_types = []
    # subpage_types = ['students.StudentHomePage']


class StudentHomePageForm(WagtailAdminPageForm):
    def __init__(self, *args, **kwargs):
        super(StudentHomePageForm, self).__init__(*args, **kwargs)

        if self.for_user and not self.for_user.is_superuser:

            if not self.instance.id:
                self.fields["institute"].queryset = Institute.objects.filter(
                    id=self.for_user.institute.id
                )

            else:
                del self.fields["institute"]


class StudentHomePage(Page):
    institute = models.OneToOneField(
        "institutes.Institute",
        related_name="student_homepage",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    welcome_title = RichTextField(null=True, blank=True)
    announcement = RichTextField(null=True, blank=True)
    # featured_title  = models.CharField(max_length=500, null=True, blank=True)

    logo = models.ForeignKey(
        "wagtailimages.Image",
        help_text="max size 1902x1100",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    template = "student/index.html"

    # @classproperty
    # def is_creatable(cls):
    #     print("IS CREATABLE???")
    #     print(cls.__dict__)
    #     return not cls.objects.exists()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        # if self.featured_products.count() > 3:
        #     raise ValidationError("You can't assign more than three featured products")
        super(StudentHomePage, self).clean(*args, **kwargs)

    def serve(self, request, *args, **kwargs):
        context = self.get_context(request)
        print("SERVE")
        context["status_code"] = 200
        if request.user.is_authenticated:

            if self.institute == request.user.institute:
                return render(request, self.get_template(request), context=context)
            else:
                home = StudentHomePage.objects.filter(
                    institute=request.user.institute
                ).first()
                if home:
                    return HttpResponseRedirect(home.full_url)

        return HttpResponseRedirect("/")

    def serve_preview(self, request, mode_name):
        # Needed for previews to work
        return self.serve(request)

    parent_page_type = ["students.StudentHomepageRoute"]
    subpage_types = []
    base_form_class = StudentHomePageForm

    class Meta:
        verbose_name = "Student HomePage"

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("institute", classname="full"),
                FieldPanel("welcome_title", classname="full"),
                FieldPanel("announcement", classname="full"),
                FieldPanel("logo", classname="full"),
            ],
            classname="collapsible",
            heading="Page Banner",
        ),
    ]
