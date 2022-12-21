from django.shortcuts import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from wagtail.admin import messages
from .models import StudentRecords


def publish(request, id):
    print("publishing")
    print(id)
    sr = StudentRecords.objects.get(id=id)
    if not request.user.is_superuser and str(request.user.role) != "Controller of Exam":
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if (
        str(request.user.role) == "Controller of Exam"
        and sr.assigned_controller != request.user
    ):
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    print(sr)
    if sr.publish:
        sr.publish = False
        sr.save()

        messages.success(
            request,
            _("{0}' Unpublish.").format(sr),
        )
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
    else:
        sr.publish = True
        sr.save()

        messages.success(
            request,
            _("{0}' Publish.").format(sr),
        )
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
