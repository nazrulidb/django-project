from django.db import models, transaction
from django.core.validators import ValidationError, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save

from modelcluster.models import ClusterableModel

from wagtail.core.models import Orderable, Collection

from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import (
    FieldPanel,
    MultiFieldPanel,
    ObjectList,
)

from django_utils.choices import Choice
from main.decorators import disable_for_loaddata

import datetime

semester_choice = ((1, "I"), (2, "II"),)
level_choices = [(1,'I'), (2,'II'), (3,'III'), (4,'IV')]

class DepartmentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("institute")


class Department(ClusterableModel, Orderable, models.Model):
    institute = ParentalKey(
        "institutes.Institute",
        null=True,
        blank=False,
        related_name="departments",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=120, null=True, blank=False)
    alternative_name = models.CharField(max_length=120, null=True, blank=False)
    custom_id = models.CharField(max_length=2, null=True, blank=True, unique=True)
    code_validator = RegexValidator(regex=r"^[a-zA-Z0-9]+$", message="String only")
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
        related_name="department_collection",
    )

    objects = DepartmentManager()

    def __str__(self):
        return f'{self.institute} - {self.name}'

    def save(self, *args, **kwargs):
        if not self.custom_id:
            latest_department = Department.objects.last()

            if latest_department:
                cus_id = int(latest_department.custom_id) + 1
                if cus_id <= 9:
                    cus_id = f"0{cus_id}"
                self.custom_id = cus_id
            else:
                self.custom_id = "01"

        elif int(self.custom_id) > 99:
            raise ValidationError({"custom_id": _("Reach instance count")})

        if not self.institute and self.department:
            self.institute = self.department.institute

        self.code = self.code.upper()
        super(Department, self).save(*args, **kwargs)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("institute"),
                FieldPanel("name"),
                FieldPanel("alternative_name"),
                FieldPanel("code"),
            ],
            heading="Department",
        ),
    ]

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        get_latest_by = "created_at"
        unique_together = ["institute", "name", "code"]


class BatchManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("department", "assigned_faculty_member", "degree")
        )


class YEARS(Choice):
    year = []
    for r in range(2000, (datetime.datetime.now().year + 2)):
        year.append((r, str(r)))
    choices = year


class Batch(ClusterableModel, Orderable):
    department = ParentalKey(
        "departments.Department",
        null=True,
        blank=False,
        related_name="department_batch",
        on_delete=models.CASCADE,
    )
    assigned_faculty_member = models.ForeignKey(
        "users.CustomUser",
        limit_choices_to={"role__name": "Faculty Member"},
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_assigned_member",
    )
    degree = models.ForeignKey(
        "institutes.Degree", on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=120, null=True, blank=False)
    year = models.IntegerField(
        choices=YEARS.choices, default=datetime.date.today().year
    )
    custom_id = models.CharField(max_length=60, null=True, blank=True, unique=True)
    id_suffix_validator = RegexValidator(regex=r"^[0-9]+$", message="Numbers only")
    suffix = models.CharField(
        validators=[id_suffix_validator], max_length=3, null=True, blank=False
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    active = models.BooleanField(default=True)
    collection = models.OneToOneField(
        Collection,
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        related_name="batch_collection",
    )

    objects = BatchManager()

    def __init__(self, *args, **kwargs):
        super(Batch, self).__init__(*args, **kwargs)

    def __str__(self):
        return f'{self.name}-{self.year}'

    def get_limit(self):
        if self.department:
            return self.department.institute
        else:
            return None

    def institute(self):
        return self.department.institute

    def get_custom_id(self):
        if self.id <= 9:
            return f"0{self.id}"
        else:
            return self.id

    class Meta:
        verbose_name = "Batch"
        verbose_name_plural = "Batches"
        get_latest_by = "created_at"
        unique_together = ["department", "name", "year"]
        ordering = ('name',)

    def clean(self, *args, **kwargs):
        if (
            self.assigned_faculty_member
            and not self.assigned_faculty_member.role.name == "Faculty Member"
        ):
            raise ValidationError("Assign role should be a faculty member.")
        
        # self.name = f'{self.name}-{self.suffix}'

        super(Batch, self).clean(*args, **kwargs)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("department"),
                FieldPanel("name"),
                FieldPanel("year"),
                FieldPanel("suffix"),
                FieldPanel("degree", classname="init-degree"),
                FieldPanel("assigned_faculty_member", classname="init-faculty-member"),
            ],
            heading="Batch",
            classname="collapsible batch-group",
        ),
    ]

    edit_handler = ObjectList(panels)

class BatchYear(ClusterableModel, Orderable):
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_department",
    )

    batch = ParentalKey(
        "departments.Batch",
        null=True,
        blank=False,
        related_name="department_batch_year",
        on_delete=models.CASCADE,
    )
    
    assigned_faculty_member = models.ForeignKey(
        "users.CustomUser",
        limit_choices_to={"role__name": "Faculty Member"},
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_member",
    )
    term = models.IntegerField(
        choices=semester_choice, default=1
    )
    level = models.IntegerField(
        choices=level_choices, default=1
    )
    year_from = models.IntegerField(
        choices=YEARS.choices, default=datetime.date.today().year
    )
    year_to = models.IntegerField(
        choices=YEARS.choices, default=(int(datetime.date.today().year)+1)
    )
    students = models.ManyToManyField(
        'users.CustomUser', verbose_name="batch_year_students", related_name="batch_year_students", blank=True, limit_choices_to={"role__name": "Student"},
    )
    collection = models.OneToOneField(Collection,on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="batch_year_collection")
    
    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        unique_together = ["batch", "level", "term", "year_to"]
        ordering = ('batch', 'level', 'year_to',)

    def __str__(self):
        return f'{self.batch.name} Level-{self.level} Term-{self.term} {self.year_to}'

    def __init__(self, *args, **kwargs):
        super(BatchYear, self).__init__(*args, **kwargs)
        
        if type(self.batch).__name__ != 'NoneType':
            self.degree = self.batch.degree
        
    def institute(self):
        return self.department.institute

    def collection_name(self):
        return f'{self.batch.name} Level-{self.level} Term-{self.term} {self.year_to}'

    def get_years(institute):
        return list(set(BatchYear.objects.filter(batch__department__institute=institute).values_list("year_to", flat=True)))

    def get_levels(institute):
        return list(set(BatchYear.objects.filter(batch__department__institute=institute).values_list("level", flat=True)))

    def get_ids(institute_id, level, year):
        return list(set(BatchYear.objects.filter(batch__department__institute__id=institute_id, level=level, year_to=year).values_list("id", flat=True)))

    @transaction.atomic
    def has_missing_instance(institute_id, level, term, year):
        batches = Batch.objects.filter(department__institute__id=institute_id).distinct('name')
        batch_years = BatchYear.objects.filter(batch__department__institute__id=institute_id, level=level,term=term, year_to=year)
      
        if batches.count() != batch_years.count():
            for batch in batches:
                BatchYear.objects.get_or_create(batch=batch, level=level,term=term,year_to=year)
            
            return True
        return False

    def clean(self, *args, **kwargs):
        if (
            self.assigned_faculty_member
            and not self.assigned_faculty_member.role.name == "Faculty Member"
        ):
            raise ValidationError("Assign role should be a faculty member.")
        
        if self.batch:
            yb = BatchYear.objects.filter(batch__name=self.batch.name, level=self.level, term=self.term, year_to=self.year_to).count()
            if yb:
                raise ValidationError("Duplicate")

        self.year_from = self.year_to - 1
        self.department = self.batch.department

        super(BatchYear, self).clean(*args, **kwargs)




@receiver(post_save, sender=Department)
@disable_for_loaddata
def department_post_save(sender, created, instance, **kwargs):
    
    from wagtail.admin.forms.collections import CollectionForm

    if created:
        parent = instance.institute.collection
        if parent:
            form = CollectionForm({'parent':parent.pk, 'name':instance.name})
            
            if form.is_valid():
                collection = form.save(commit=False)
                parent.add_child(instance=collection)
                collection.save()

                instance.collection = collection
                instance.save(update_fields=['collection'])

                institute_collections = instance.institute.get_collections()
                institute_collections.collection.add(collection)
     

@receiver(post_save, sender=Batch)
@disable_for_loaddata
def batch_post_save(sender, created, instance, **kwargs):
    
    from wagtail.admin.forms.collections import CollectionForm

    if created:
        parent = instance.department.collection

        if parent:
            existing_collection = Collection.objects.filter(name=instance.name).first()
            if not existing_collection:
                form = CollectionForm({'parent':parent.pk, 'name':instance.name})
                if form.is_valid():
                    collection = form.save(commit=False)
                    parent.add_child(instance=collection)
                    collection.save()

                    instance.collection = collection
                    instance.save(update_fields=['collection'])

                    institute_collections = instance.department.institute.get_collections()
                    institute_collections.collection.add(collection)
    else:
        if instance.name != instance.collection.name:
            prev_name = instance.collection.name

            instance.collection.name = instance.name
            instance.collection.save()

            des = instance.collection.get_descendants()
            if des:
                for d in des:
                    name = d.name.replace(prev_name, instance.name)
                    d.name = name
                    d.save(update_fields=["name"])

        batch_year = BatchYear.objects.filter(batch=instance).first()
        if batch_year and batch_year.assigned_faculty_member != instance.assigned_faculty_member:
            batch_year.assigned_faculty_member = instance.assigned_faculty_member
            batch_year.save(update_fields=["assigned_faculty_member"])

@receiver(post_save, sender=BatchYear)
@disable_for_loaddata
def batch_year_post_save(sender, created, instance, **kwargs):
    
    from wagtail.admin.forms.collections import CollectionForm

    if created:
        parent = instance.batch.collection
        if parent:
            name = f'{parent.name} Level-{instance.level} Term-{instance.term} {instance.year_to}'

            yb_collection = Collection.objects.filter(name=name).first()

            if not yb_collection:
                form = CollectionForm({'parent':parent.pk, 'name':name})
                
                if form.is_valid():
                    collection = form.save(commit=False)
                    parent.add_child(instance=collection)
                    collection.save()
                    instance.collection = collection
                    instance.save(update_fields=["collection"])

                    institute_collections = instance.batch.department.institute.get_collections()
                    institute_collections.collection.add(collection)

        if instance.batch.assigned_faculty_member:
            instance.assigned_faculty_member = instance.batch.assigned_faculty_member
            instance.save(update_fields=["assigned_faculty_member"])
    else:
        batch = instance.batch
        if batch and batch.assigned_faculty_member != instance.assigned_faculty_member:
            batch.assigned_faculty_member = instance.assigned_faculty_member
            batch.save(update_fields=["assigned_faculty_member"])
