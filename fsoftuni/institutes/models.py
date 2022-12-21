from django.db import models, transaction
from django.conf import settings
from django.core.validators import ValidationError, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.core.exceptions import (
    PermissionDenied,
)
from asgiref.sync import sync_to_async, async_to_sync
from modelcluster.models import ClusterableModel

from wagtail.core.models import Orderable
from modelcluster.fields import ParentalKey

from wagtail.documents.models import Document, AbstractDocument
from wagtail.core.models import Collection
from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
)

from institutes.excel_extract import Extractor
from custom_dashboard.models import StudentRecords
import json, threading
from threading import current_thread
from main.decorators import disable_for_loaddata
class InstituteCollections(models.Model):
    institute = models.OneToOneField(
        'institutes.Institute',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="intitute_collections",
    )
    collection = models.ManyToManyField(
        Collection, related_name="+", blank=True)

    def __str__(self):
        return f'{self.institute} Collections'
    
class Institute(ClusterableModel, Orderable, models.Model):
    name = models.CharField(max_length=120, null=True, blank=False, unique=True)
    custom_id = models.CharField(max_length=2, null=True, blank=True, unique=True)
    code_validator = RegexValidator(regex=r"[a-zA-Z]", message="String only")
    code = models.CharField(
        validators=[code_validator], max_length=3, null=True, blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    active = models.BooleanField(default=True)
    collection = models.OneToOneField(
        Collection,
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        related_name="collection_key",
    )

    def __str__(self):
        return str(self.name)

    def get_collections(self):
        collection = InstituteCollections.objects.filter(institute=self).first()
        return collection

    def save(self, *args, **kwargs):
        if not self.custom_id:
            latest_institute = Institute.objects.last()

            if latest_institute:
                cus_id = int(latest_institute.custom_id) + 1
                if cus_id <= 9:
                    cus_id = f"0{cus_id}"
                self.custom_id = cus_id
            else:
                self.custom_id = "01"

        elif int(self.custom_id) > 99:
            raise ValidationError({"custom_id": _("Reach instance count")})
        self.code = self.code.upper()
        super(Institute, self).save(*args, **kwargs)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("code"),
            ],
            heading="Institute",
            classname="collapsible",
        ),
        
    ]

    class Meta:
        verbose_name = "Institute"
        verbose_name_plural = "Institutes"
        get_latest_by = "created_at"
        

@receiver(post_save, sender=Institute)
@disable_for_loaddata
def institute_post_save(sender, created, instance, **kwargs):
    
    from wagtail.admin.forms.collections import CollectionForm

    if created:
        print('created')
        institute_collections = InstituteCollections.objects.create(institute=instance)
 
        root = Collection.objects.first()
        form = CollectionForm({'parent':root.pk, 'name':instance.name})
        if form.is_valid():
            collection = form.save(commit=False)
            root.add_child(instance=collection)
            collection.save()
            
            instance.collection = collection
            instance.save(update_fields=['collection'])

            institute_collections.collection.add(collection)

        # print(f'institute_collection {institute_collection}')
    else:
        if instance.name != instance.collection.name:
            collection = instance.collection
            collection.name = instance.name
            collection.save()


class Degree(ClusterableModel, Orderable, models.Model):
    institute = ParentalKey(
        "institutes.Institute",
        null=True,
        blank=False,
        related_name="degrees",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=120, null=True, blank=False)
    custom_id = models.CharField(max_length=2, null=True, blank=True, unique=True)
    code_validator = RegexValidator(
        regex=r"^[a-zA-Z0-9]+$", message="Alphanumeric only"
    )
    code = models.CharField(
        validators=[code_validator], max_length=3, null=True, blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if not self.custom_id:
            latest_department = Degree.objects.last()

            if latest_department:
                cus_id = int(latest_department.custom_id) + 1
                if cus_id <= 9:
                    cus_id = f"0{cus_id}"
                self.custom_id = cus_id
            else:
                self.custom_id = "01"

        elif int(self.custom_id) > 99:
            raise ValidationError({"custom_id": _("Reach instance count")})

        self.code = self.code.upper()
        super(Degree, self).save(*args, **kwargs)

    panels = [
        FieldPanel("institute"),
        FieldPanel("name"),
        FieldPanel("code"),
    ]


def data_default():
    return {
        "sheets": [],
        "excel_data": {},
        "student_records":{},
        "student_records_id":None,
        "error_message":None,
    }



# @register_snippet
class CustomDocument(AbstractDocument):
    # Custom field example:
    institute = models.ForeignKey(
        'institutes.Institute',
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        related_name="institute_documents",
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        related_name="department_documents",
    )
    batch = models.ForeignKey(
        'departments.BatchYear',
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        related_name="batch_documents",
    )
    data = models.JSONField(default=data_default, null=True, blank=True)
    prev_hash = models.CharField(max_length=40, null=True, blank=True)
    # admin_form_fields = Document.admin_form_fields + ()
    has_task = models.BooleanField(default=False)

    admin_form_fields = ('title', 'file', 'institute')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def delete(self, force=False):
        print("HERE ON DELETE")
        if force:
            self.delete()
        else:
            raise PermissionDenied

    def clean(self, *args, **kwargs):
        print("CUSTOM DOCUMENT CLEAN!")

        if type(self.institute).__name__ != "NoneType" and self.uploaded_by_user.institute:
            if not self.institute:
                self.institute = self.uploaded_by_user.institute

        if not self.collection and self.institute:
            self.collection = self.institute.collection

        super(CustomDocument, self).clean(*args, **kwargs)

    def get_data(self):
        if type(self.data).__name__ == "str":
            return json.loads(self.data)
        else:
            return self.data
    
    def dumps(self, data):
        return json.dumps(data)

    @transaction.atomic
    def extract_data(self, record):
        print('extract_data')
        print(f'record {record}')
        f_data = self.get_data()
        sid = transaction.savepoint()
        try:
            
            with transaction.atomic():

                if settings.DEBUG:
                    if settings.DEBUG_PROD:
                        extract = Extractor(self.file.storage.url(self.file.name), record, self.institute.id)
                    else:
                        extract = Extractor(self.file.storage.path(self.file.name), record, self.institute.id)
                else:
                    extract = Extractor(self.file.storage.url(self.file.name), record, self.institute.id)

  
            d = extract.get_data()
    
            f_data["sheets"] = d[0]
            f_data["excel_data"] = d[1]
            details = d[2].pop('details')
            f_data["student_records"] = d[2]
            f_data["details"] = details
            
            record.status = 'pending'
            record.save(update_fields=["status"])
            transaction.savepoint_commit(sid)
        except Exception as e:
            transaction.savepoint_rollback(sid)
            with transaction.atomic():
                record.status = 'invalid'
                record.save(update_fields=["status"])
                
            print("ERRROR!!!")
            print(e)
            print(type(e))
            f_data["error_message"] = str(e)

        self.has_task = False
        try:
            f_data = self.dumps(f_data)
            self.data = f_data
            with transaction.atomic():
                self.save()
        except Exception as e:
            print("FAILLLL!")
            self.data = f_data 
            with transaction.atomic():
                self.save()
        
        
        print('EXTRACT DATA END>')

        
@disable_for_loaddata
@receiver(pre_save, sender=CustomDocument)
def custom_doc_post_save(sender, instance, **kwargs):
    print("custom_doc_post_save END!!!!")
            
