# Generated by Django 4.0.5 on 2022-07-22 23:55

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('departments', '0011_alter_department_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='code',
            field=models.CharField(max_length=3, null=True, validators=[django.core.validators.RegexValidator(message='String only', regex='^[a-zA-Z0-9]+$')]),
        ),
    ]
