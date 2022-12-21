from django.http import JsonResponse
from django.db.models import CharField, Value
from django.db.models.functions import Concat
from django.db.models import Q

from institutes.models import Degree
from users.models import CustomUser
from django.contrib.auth.decorators import login_required


@login_required
def batch_filter(request):
    print("batch_filter")
    print()
    print(request.GET.get("model_name"))
    id = request.GET.get("id")
    model_name = request.GET.get("model_name")
    q = Q(institute__id=id)

    if not request.user.is_superuser:
        q = Q(institute__id=request.user.department.institute.id)
    else:
        q = Q(institute__id=0)

    degrees = Degree.objects.values("id", "name").filter(q)
    members = (
        CustomUser.objects.annotate(
            name=Concat("first_name", Value(" "), "last_name", output_field=CharField())
        )
        .values("id", "name")
        .filter(role__name="Faculty Member")
        .filter(q)
    )

    print(degrees)
    print(members)
    return JsonResponse(
        {"status": 200, "dataDegree": list(degrees), "dataMember": list(members)},
        safe=False,
    )
