from wagtail.admin.forms.models import WagtailAdminModelForm

from django import forms
from django.contrib.auth import get_user_model

Users = get_user_model()

from departments.models import BatchYear
from .models import StudentRecords, BatchUploadResult


status_choice = (("decline", "Decline"), ("approve", "Approve"))

upload_order = {
    (1, 1):(1, 2),
    (1, 2):(2, 1),
    (2, 1):(2, 2),
    (2, 2):(3, 1),
    (3, 1):(3, 2),
    (3, 2):(4, 1),
    (4, 1):(4, 2),
}

string_value = {
    1:1,
    2:2,
    3:3,
    4:4
}

class StudentRecordsForm(WagtailAdminModelForm):
    class Meta:
        model = StudentRecords
        fields = [
            "assigned_pr",
            "exam_held",
            "level",
            "term",
            "year",
            "link_document",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.for_user = kwargs.get("for_user")

        self.fields["link_document"].accept = ".xls,.xlsx"
        self.fields["link_document"].required = True
        self.fields["year"].required = True
        self.fields["year"].label = 'Admission Year'
        self.fields["assigned_pr"].required = True

        print("StudentRecordsForm")
        
        if not self.for_user.is_superuser:
            # batch_years = BatchYear.get_years(self.for_user.institute)
            # choices = []
            # for y in batch_years:
            #     choices.append((y,y))
            # self.fields["year"].choices = choices
            # levels = BatchYear.get_levels(self.for_user.institute)
            # choices = []
            # for y in levels:
            #     choices.append((y,y))
            # self.fields["level"].choices = choices

            self.fields["assigned_pr"].queryset = Users.objects.filter(institute=self.for_user.institute, role__name="Proof Reader of Exam")
    
    def clean(self):
        cleaned_data = super(StudentRecordsForm, self).clean()
        if self.is_valid():
            print(cleaned_data)
            level = cleaned_data["level"]
            term = cleaned_data["term"]
            year = cleaned_data["year"]

            has_missing_instance = BatchYear.has_missing_instance(self.for_user.institute.id, level, term, year)
            # if has_missing_instance:
            #     raise forms.ValidationError(f"Batch and BatchYear count did'nt match please make sure that all of the Batch have an instance of Level:{level} and Year:{year}")
            
            batch_year_uploads = StudentRecords.objects.filter(institute=self.for_user.institute,term=term,level=level, year=year).count()
            print(f'batch_year_uploads {batch_year_uploads}')
            if batch_year_uploads:
                raise forms.ValidationError("Maximum upload count for level, term, year")

            
            m = None
            last_upload = StudentRecords.objects.filter(institute=self.for_user.institute, year=year).last()
            if last_upload:
                prev = upload_order.get( (last_upload.level, last_upload.term) )
                if prev:
                    l,t = prev
                    if l != level or t != term:
                        m = f'Level and term for {year} are way too far to the previous batch upload \n previous Level-{last_upload.level} Term-{last_upload.term} next should be Level={l} Term-{t}'
           
            else:
                l, t = [1,1]
                if l != level or t != term:
                    m = f'First upload for this admission year should be Level-1 Term-1'

            if m:
                self.fields["level"].choices = [(l,string_value.get(l))]
                self.fields["term"].choices = [(t,string_value.get(t))]
                
                raise forms.ValidationError(m)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save()

        instance.institute = self.for_user.institute
        instance.assigned_controller = self.for_user
        instance.updated_by = self.for_user
        batch_ids = BatchYear.get_ids(instance.institute.id, instance.level, instance.year)
        instance.batches.add(*batch_ids)

        if commit:
            instance.save()
            print("SAVING")

        
        return instance


class StudentRecordsEditForm(WagtailAdminModelForm):
    class Meta:
        model = StudentRecords
        fields = [
            "assigned_controller",
            "assigned_pr",
            "status",
            "comment",
            "link_document",
            "exam_held",
            "level",
            "term",
            "year",
            "approve_at",
        ]

    def __init__(self, *args, **kwargs):
        print("EDIT BATCH FILES")
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        self.for_user = kwargs.get("for_user")
        print(f'instance {instance}')
        self.fields["term"].disabled = True
        self.fields["level"].disabled = True
        self.fields["year"].label = 'Admission Year'

        if not instance.publish:
            self.fields["link_document"].accept = ".xls,.xlsx"
            self.fields["link_document"].required = True
            self.fields["year"].disabled = True
            
            del self.fields["assigned_controller"]
            del self.fields["assigned_pr"]
            del self.fields["approve_at"]

            # self.fields["year"].disabled = True

            if str(self.for_user.role) == "Proof Reader of Exam":
                
                self.fields["status"].required = True
                self.fields["status"].choices = status_choice
                self.fields["status"].initial = None

                self.fields["exam_held"].label = ''
                self.fields["link_document"].label = ''
                self.fields["level"].label = ''
                self.fields["term"].label = ''
                self.fields["year"].label = ''

                self.fields["exam_held"].widget = forms.HiddenInput()
                self.fields["link_document"].widget = forms.HiddenInput()
                self.fields["level"].widget = forms.HiddenInput()
                self.fields["term"].widget = forms.HiddenInput()
                self.fields["year"].widget = forms.HiddenInput()

                

            if str(self.for_user.role) == "Controller of Exam":
                del self.fields["status"]
                
                if instance.status == "approve":
                    self.fields["link_document"].disabled = True
        else:
            fields = [
                "assigned_controller",
                "assigned_pr",
                "status",
                "year",
                "comment",
                "link_document",
                "approve_at",
            ]

            for field in fields:
                self.fields[field].disabled = True


    def clean(self):
        cleaned_data = super(StudentRecordsEditForm, self).clean()
        print("cleaned_data")
        print(cleaned_data)
        if self.is_valid():
            print(cleaned_data)
            level = cleaned_data["level"]
            year = cleaned_data["year"]
            term = cleaned_data["term"]
            BatchYear.has_missing_instance(self.for_user.institute.id, level,term, year)
            # if has_missing_instance:
            #     raise forms.ValidationError(f"Batch and BatchYear count did'nt match please make sure that all of the Batch have an instance of Level:{level} and Year:{year}")
            
            batch_year_uploads = StudentRecords.objects.filter(institute=self.for_user.institute,term=term,level=level, year=year).count()
            if batch_year_uploads and batch_year_uploads > 2:
                raise forms.ValidationError("Maximum upload count for batch year")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save()

        instance.updated_by = self.for_user
        batch_ids = BatchYear.get_ids(instance.institute.id, instance.level, instance.year)
        instance.batches.add(*batch_ids)

        if instance.status == "invalid" and self.for_user == instance.assigned_controller:
            doc = instance.link_document
            if doc.file_hash != doc.prev_hash:
                instance.status = "pending"

        if commit:
            instance.save()
            print("SAVING")

        print(instance.institute)
        return instance


class CertGenForm(WagtailAdminModelForm):
    date = forms.CharField(required=False)
    class Meta:
        model = BatchUploadResult
        fields = [
            "students",
            "certificates",
            "date",
        ]
        widgets = {
            "students": forms.CheckboxSelectMultiple(),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        self.for_user = kwargs.get("for_user")
        self.fields['students'].queryset = instance.students.all()



    
    # def save(self, commit=False):
    #     print('CERT SAVING!!!')
    #     instance = super().save()
    #     students = instance.students.all()
    #     print(f'students {students}')
    #     students_id = list(students.values_list("id", flat=True))
    #     print(f'students_id {students_id}')
    #     student_records = StudentRecord.objects.filter(student__id__in=students_id)
    #     print(f'student_records {student_records}')

    #     for record in student_records:
    #         print(record.get_data_for_provisional_cert())
   
    #     return instance

