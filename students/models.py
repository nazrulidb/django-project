from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from wagtail.core.models import Orderable
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel

from modelcluster.models import ClusterableModel

class StudentProfileManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("user")


class StudentProfile(models.Model):
    user = models.OneToOneField(
        "users.CustomUser",
        null=False,
        blank=False,
        related_name="student_profile",
        on_delete=models.CASCADE,
    )
    objects = StudentProfileManager()
    prev_batch = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prev_batch = str(self.user.batch)

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        super().save(force_insert, force_update, *args, **kwargs)
        self.prev_batch = str(self.user.batch)

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"

    def degree(self):
        return self.batch.degree

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"


def data_default():
    return {}


class StudentRecord(ClusterableModel, Orderable):
    student = models.ForeignKey(
        "users.CustomUser",
        limit_choices_to={"role__name": "Student"},
        null=True,
        blank=False,
        related_name="student_report",
        on_delete=models.SET_NULL,
    )
    record = models.ForeignKey(
        "custom_dashboard.StudentRecords",
        null=False,
        blank=False,
        related_name="student_record",
        on_delete=models.CASCADE,
    )
    result = models.ForeignKey(
        "custom_dashboard.BatchUploadResult",
        null=True,
        blank=False,
        related_name="student_record_result",
        on_delete=models.CASCADE,
    )
    publish = models.BooleanField(default=False)
    data = models.JSONField(default=data_default)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    year_gap = models.BooleanField(default=False)
    retake = models.BooleanField(default=False)
    has_retake = models.BooleanField(default=False)
    term = models.IntegerField(default=1)
    level = models.IntegerField(default=1)
    year = models.IntegerField(null=True)

    class Meta:
        verbose_name = "Student Record"
        verbose_name_plural = "Student Records"

    def __str__(self):
        return f"{self.student} Level-{self.level} Term-{self.term} {self.record.year}"

    def get_data_for_provisional_cert(self):
        data = {}
        data['cgpa'] = self.data.get('CGPA')
        data['full_name'] = f'{self.student.first_name} {self.student.last_name}'
        data['department'] = f'{self.student.department.alternative_name}'
        data['year'] = self.record.year
        data['degree'] = self.student.batch.degree.name
        return data

    def exam_held(self):
        return self.record.exam_held
    
    def get_subjects(self, source=None):
        print("get_result")
        if not source:
            source = self.data
            
        if source:
            subjects = source.get("Subjects")
            data_list = []
            ctr = 1
            for k, v in subjects.items():
                data = {"subject": k, "no": ctr}
                for r, v in v.items():
    
                    data[r.lower().replace(" ", "_")] = v
                data_list.append(data)
                ctr += 1
                # print(v)

            return data_list
    
    def get_subject_headers(self):
        source = self.data
        if source:
            subjects = source.get("Subjects")

     
            data = {
                "total_credits_completed_in_this_term": "",
                "total_credits_taken_in_this_term": "",
                "failed_subject": "",
                "result": "",
                "term_gpa": "",
                "cgpa": "",
            }
            for k, item in source.items():

                if not k == "Subjects":
                    f = k.lower().replace("  ", "_").replace(" ", "_")
                    if f.startswith("total_credits_taken_in_this_term"):
                        data["total_credits_taken_in_this_term"] = item
                    if f.startswith("total_credits_completed_in_this_term"):
                        data["total_credits_completed_in_this_term"] = item
                    if f.startswith("failed_subject"):
                        data["failed_subject"] = item
                    if f.startswith("result"):
                        data["result"] = item
                    if f.startswith("cgpa"):
                        data["cgpa"] = item
                    if f.endswith("gi_of_the_term"):
                        data["term_gpa"] = item

            return data
    def has_retake_result(self):
        result = self.data.get('retake_result')
        if result:
            return True
        return False
    
    def retake_info(self):
        return self.data.get('retake_result')
    
    def retake_subject(self):
        result = self.data.get('retake_result')
        return self.get_subjects(result)
        
@receiver(post_save, sender=StudentRecord)
def student_record_post_save(sender, created, instance, **kwargs):
    if created:
        if instance.retake:
            print("HANDLING RETAKE....")
            sr = StudentRecord.objects.filter(
                student=instance.student, 
                record__level=instance.record.level, 
                record__term=instance.record.term,
                has_retake=True
            ).first()

            if sr:
                retake_res = instance.data
                sr.data['retake_result'] = retake_res
                sr.save()


@receiver(post_save, sender=StudentProfile)
def student_profile_created(sender, created, instance, **kwargs):
    if created:
        institute_code = instance.batch.department.institute.code
        year = instance.batch.year
        degree_custom_id = instance.batch.degree.custom_id
        department_custom_id = instance.batch.department
        suffx = instance.user.suffix
        instance.user.username = (
            f"{institute_code}{year}{degree_custom_id}{department_custom_id}{suffx}"
        )
        instance.user.save()
