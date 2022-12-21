from django.db import models
from django.core.validators import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.utils.formats import localize
from django.utils.translation import gettext_lazy as _
from django import forms

from modelcluster.models import ClusterableModel

from wagtail.core.models import Orderable, Collection
from wagtail.documents import get_document_model
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, ObjectList
from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import (
    FieldPanel,
)
from wagtail.core.fields import RichTextField
from django.contrib.auth import get_user_model
from students.models import StudentRecord
from departments.models import BatchYear, YEARS
from main.decorators import disable_for_loaddata
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()
channel_layer = get_channel_layer()

status_choice = (("pending", "Pending"), ("decline", "Decline"), ("approve", "Approve"), ("processing", "Processing"), ("invalid", "Invalid"))
year_choice = [(2022,2022), (2023,2023)]
semester_choice = ((1, "I"), (2, "II"),)
level_choices = [(1,1), (2,2), (3,3), (4,4)]

def data_default():
    return {
        "is_lock": False,
        "prev_status": None,
        "comments": "",
        "document": {},
        "is_publish": False,
    }


class RecordsManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "institute", "assigned_controller", "assigned_pr", "link_document"
            )
        )



class StudentRecords(ClusterableModel, Orderable, models.Model):
    institute = ParentalKey(
        "institutes.Institute",
        null=True,
        blank=False,
        related_name="institute_student_records",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    assigned_controller = models.ForeignKey(
        "users.CustomUser",
        limit_choices_to={"role__name": "Controller of Exam"},
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_controller",
        verbose_name="Controller of Exam",
    )
    assigned_pr = models.ForeignKey(
        "users.CustomUser",
        limit_choices_to={"role__name": "Proof Reader of Exam"},
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_proof_reader",
        verbose_name="Proof Reader of Exam",
    )
    link_document = models.OneToOneField(
        "institutes.CustomDocument",
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.CASCADE,
    )
    term = models.IntegerField(
        choices=semester_choice, default=1
    )
    level = models.IntegerField(
        choices=level_choices, default=1
    )
    exam_held = models.IntegerField(null=True, blank=False, choices=YEARS.choices)
    year = models.IntegerField(null=True, blank=False, choices=YEARS.choices)
    batches = models.ManyToManyField(
        "departments.BatchYear",
        related_name="student_record_year_batch",
        verbose_name="Batches",
    )
    updated_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_by",
        verbose_name="Updated by",
    )

    active = models.BooleanField(default=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    comment = RichTextField(null=True, blank=True)
    approve_at = models.DateTimeField(null=True)
    
    status = models.CharField(choices=status_choice, default="processing", max_length=50)
    data = models.JSONField(default=data_default)
    
    timestamp = models.DateTimeField(auto_now=True)
    publish = models.BooleanField(default=False)
    objects = RecordsManager()

    class Meta:
        verbose_name = "Student Batch Record"
        verbose_name_plural = "Student Batch Records"
        unique_together = ["institute", "year", "term", "level"]

    def delete(self, force=False):
        BatchUploadResult.objects.filter(batch_file=self).delete()
        self.link_document.delete()
        super(StudentRecords, self).delete()


    def clean(self, *args, **kwargs):
        print(f"StudentRecords ID={self.id}")
        print(self.assigned_controller)
        if not self.name:
            self.name = str(self.link_document)
            self.data["is_lock"] = True
            
        if self.status == "approve":
            self.approve_at = datetime.now()
        
        if self.data.get('prev_status') == "invalid" and self.link_document.file_hash == self.link_document.prev_hash:
            raise ValidationError("Batch file didn't change.")

        if (
            self.assigned_controller
            and not self.assigned_controller.role.name == "Controller of Exam"
        ):
            raise ValidationError("Assign role should be a Controller of Exam.")

        if (
            self.assigned_pr
            and not self.assigned_pr.role.name == "Proof Reader of Exam"
        ):
            raise ValidationError("Assign role should be a Proof Reader of Exam.")
        
        if self.status == "decline" and not self.comment:
            raise ValidationError("Please add a comment.")


        lock = ['approve', 'processing']
        if self.status in lock:
            self.data["is_lock"] = True
            
        else:
            self.data["is_lock"] = False

        self.data["prev_status"] = self.status

    def __str__(self):
        return f"Batch Record - Level-{self.level} Term-{self.term} {self.year} Held-{self.exam_held}"

    def get_record_count(self):
        return str(StudentRecord.objects.filter(record=self).count())

    def extract_timeout(self):
        if self.status == "processing":
            n = datetime.now() - self.timestamp
            if 600 < n.total_seconds():
                return True
        return False

        

certs = (('Provisional', 'Provisional'),)
def batch_data():
    return {
        "certificate_issued":[],
    }
class BatchUploadResult(ClusterableModel, Orderable, models.Model):
    batch_file = ParentalKey(
        StudentRecords,
        null=True,
        blank=False,
        related_name="institute_student_records",
        on_delete=models.SET_NULL,
    )
    students = models.ManyToManyField(
        'users.CustomUser', related_name="batch_upload_result", blank=True, limit_choices_to={"role__name": "Student"},
    )
    collection = models.OneToOneField(Collection,on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+")
    batch_year = models.ForeignKey(
        "departments.BatchYear",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    certificates = models.CharField(choices=certs, max_length=50, default="Provisional")
    date = models.CharField(null=True, blank=False, max_length=120)
    data = models.JSONField(default=batch_data)

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificate Generator"
        unique_together = ["batch_file", "batch_year"]
    def __str__(self):
        return str(self.batch_year)

    edit_handler = ObjectList([
        FieldPanel('certificates'),
        FieldPanel('date'),
        FieldPanel('students',  widget=forms.CheckboxSelectMultiple),
    ])

@receiver(post_save, sender=BatchUploadResult)
def record_post_save(sender, instance, *args, **kwargs):
    from wagtail.admin.forms.collections import CollectionForm

    
    parent = instance.batch_year.collection
    if parent and not instance.collection:
        name = f'{parent.name} - Files'
        existing_collection = Collection.objects.filter(name=name).first()
        if not existing_collection:
            form = CollectionForm({'parent':parent.pk, 'name':name})
            
            if form.is_valid():
                collection = form.save(commit=False)
                parent.add_child(instance=collection)
                collection.save()
                instance.collection = collection
                instance.save()
        elif existing_collection and not instance.collection:
            instance.collection = existing_collection
            instance.save()

@receiver(post_save, sender=StudentRecords)
def record_post_save(sender, instance, created, *args, **kwargs):
    Document = get_document_model()
    doc = Document.objects.filter(id=instance.link_document.id).first()
    f_data = doc.get_data()

    if doc.prev_hash != doc.file_hash:
        doc.has_task = True

    if instance.id:
        f_data['student_records_id'] = instance.id


    if created:
        print("StudentRecords CREATED")
        doc.has_task = True
        # f_data['student_records_id'] = instance.id

        # doc.department = instance.batch_year.batch.department
        # doc.collection = instance.batch_year.collection
        # doc.batch = instance.batch_year
        # instance.status = 'pending'
        # instance.save(update_fields=["status"])
        
        
    else:
        
        if instance.data.get("is_publish") != instance.publish:
            print("publish state change")
            
            records = StudentRecord.objects.filter(record=instance).update(
                publish=instance.publish
            )
            print(f"updated {records}")

            instance.data["is_publish"] = instance.publish
            # instance.save(update_fields=["data"])
            StudentRecords.objects.filter(id=instance.id).update(data=instance.data)
            batch_result = BatchUploadResult.objects.filter(batch_file=instance)
            if instance.publish and not batch_result:
                batches_year = instance.batches.all()
                print("PUSBLISH AND BATCH RESULT")
                for batchyear in batches_year:
                    print(f'batchyear {batchyear}')
                    try:
                        br, is_created = BatchUploadResult.objects.get_or_create(batch_file=instance, batch_year=batchyear)
                    except:
                        is_created = False
                        
                    if is_created:
                        StudentRecord.objects.filter(record=instance).update(result=br)
                        student_ids = list(StudentRecord.objects.filter(result=br, record=instance).values_list("student__id", flat=True))
                        br.students.add(*student_ids)
                        batchyear.students.add(*student_ids)
                        print(f'student_ids {student_ids}')


        if instance.comment:
            comment = f"{instance.updated_by} - {localize(instance.timestamp)} <br> {instance.comment}<br><br>"
            instance.comment = ""
            if not instance.data["comments"]:
                instance.data["comments"] = ""

            instance.data["comments"] += comment
            # instance.save(update_fields=["comment"])
            StudentRecords.objects.filter(id=instance.id).update(data=instance.data, comment="")
    
    
    if doc.has_task:
        
        print("ENTERING TASK!")
        doc.has_task = False
        print(f'institute {doc.institute}')
        
        print('construct!!')
        
        async_to_sync(
            channel_layer.group_send)(
                'global', {
                    "type": "extract.data",
                    "document_id":doc.id,
                    "record_id":instance.id
            })
        

        print("SHOULD SEND TO CONSUMER")
    doc.prev_hash = doc.file_hash
    doc.data = doc.dumps(f_data)
    doc.save()