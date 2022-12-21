from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib.auth import login as auth_login, logout
from django.urls import reverse
from django.http import HttpResponseRedirect
from .page import StudentHomePage
from .forms import StudentLogin


def student_home(request):
    context = {}
    return render(request, "student/index.html", context)


class StudentLogin(LoginView):
    template_name = "student/login_form.html"

    # next_page = ""
    authentication_form = StudentLogin

    def form_valid(self, form):
        """Security check complete. Log the user in."""

        student_homepage = StudentHomePage.objects.filter(
            institute=form.get_user().institute
        ).first()
        print(student_homepage.full_url)
        print(student_homepage.url)
        print(student_homepage.get_full_url())
        print(student_homepage.__dict__)
        # url_path = StudentHomePage.reverse_subpage('institute_student_homepage', args=(student_homepage.id, ))

        auth_login(self.request, form.get_user())
        return HttpResponseRedirect(student_homepage.url)


def user_logout(request):
    logout(request)
    return HttpResponseRedirect("%s" % (reverse("student_login")))
