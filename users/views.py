from django.http import JsonResponse
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required

from institutes.models import Institute
from departments.models import Department, Batch, BatchYear
from .models import CustomGroup

# Create your views here.
@login_required
def get_listing(request):
    data = []
    data2 = []

    if request.user.is_superuser:
        group_qset = Group.objects.all()
        institute_qset = Institute.objects.all()
    else:
        custom_group = CustomGroup.objects.filter(role=request.user.role).first()
        group_qset = custom_group.roles.all().exclude(name="Super User").exclude(name="Student")
        institute_qset = Institute.objects.filter(id=request.user.institute.id)

    for item in group_qset:
        custom_id = item.id
        if item.id <= 9:
            custom_id = f"0{item.id}"

        data.append(
            {
                "id": item.id,
                "name": item.name,
                "custom_id": custom_id,
            }
        )

    for item in institute_qset:
        data2.append({"id": item.id, "name": item.name, "custom_id": item.code})

    return JsonResponse({"status": 200, "roles": data, "institutes": data2}, safe=False)


@login_required
def get_student_listing(request):
    data = []
    data2 = []
    data3 = []
    if (
        request.method == "POST"
        and request.user.is_superuser
        or str(request.user.role) == "Faculty Member"
    ):
        institute_id = request.POST.get("institute_id")
        department_id = request.POST.get("department_id")

        if request.user.is_superuser:
            if department_id:
                batch_qset = BatchYear.objects.filter(batch__department__id=int(department_id))

                for i in batch_qset:
                    if i.batch.degree.id <= 9:
                        custom_id = f"0{i.batch.degree.id}"
                    data2.append(
                        {
                            "year": i.year,
                            "degree_id": custom_id,
                            "id": i.batch.id,
                            "name": i.batch.name+" "+i.batch.suffix,
                        }
                    )

            else:
                inst_qset = Institute.objects.all()
                for i in inst_qset:
                    data3.append({"id": i.id, "code": i.code, "name": i.name})

                if institute_id:
                    dept_qset = Department.objects.filter(
                        institute__id=int(institute_id)
                    )
                    for i in dept_qset:
                        data.append(
                            {"id": i.id, "custom_id": i.custom_id, "name": i.name}
                        )

        if str(request.user.role) == "Faculty Member":
            data3.append(
                {
                    "id": request.user.institute.id,
                    "code": request.user.institute.code,
                    "name": request.user.institute.name,
                }
            )
            data.append(
                {
                    "id": request.user.department.id,
                    "custom_id": request.user.department.code,
                    "name": request.user.department.name,
                }
            )

            for i in Batch.objects.filter(assigned_faculty_member=request.user):
                if i.degree.id <= 9:
                    custom_id = f"0{i.degree.id}"
                    data2.append(
                        {
                            "year": i.year,
                            "degree_id": custom_id,
                            "id": i.id,
                            "name": i.name+" "+i.suffix,
                        }
                    )

        return JsonResponse(
            {"status": 200, "institutes": data3, "departments": data, "batches": data2},
            safe=False,
        )


@login_required
def department_list(request):
    id = request.GET.get("id")

    departments = Department.objects.filter(institute__id=id)

    if departments:
        data = []
        for item in departments:
            data.append({"id": item.id, "name": item.name, "custom_id": item.custom_id})
        return JsonResponse({"status": 200, "departments": data}, safe=False)
