# Generated by Django 4.0.5 on 2022-09-18 20:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('departments', '0018_alter_batchyear_level'),
        ('custom_dashboard', '0018_alter_studentrecords_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='batchuploadresult',
            name='batch_year',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='departments.batchyear'),
        ),
    ]
