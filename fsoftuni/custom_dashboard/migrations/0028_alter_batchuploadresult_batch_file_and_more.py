# Generated by Django 4.0.8 on 2022-11-16 20:11

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('institutes', '0011_customdocument_has_task'),
        ('custom_dashboard', '0027_alter_studentrecords_exam_held'),
    ]

    operations = [
        migrations.AlterField(
            model_name='batchuploadresult',
            name='batch_file',
            field=modelcluster.fields.ParentalKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='institute_student_records', to='custom_dashboard.studentrecords'),
        ),
        migrations.AlterField(
            model_name='studentrecords',
            name='link_document',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='institutes.customdocument'),
        ),
    ]
