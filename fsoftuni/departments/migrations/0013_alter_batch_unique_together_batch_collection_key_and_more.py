# Generated by Django 4.0.5 on 2022-08-31 16:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0069_log_entry_jsonfield'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('departments', '0012_alter_department_code'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='batch',
            unique_together={('department', 'name')},
        ),
        migrations.AddField(
            model_name='batch',
            name='collection_key',
            field=models.CharField(max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='collection_key',
            field=models.CharField(max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name='batch',
            name='assigned_faculty_member',
            field=models.ForeignKey(blank=True, limit_choices_to={'role__name': 'Faculty Member'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='current_assigned_member', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(
            model_name='batch',
            name='year',
        ),
        migrations.CreateModel(
            name='BatchYear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('year_from', models.IntegerField(choices=[(2000, '2000'), (2001, '2001'), (2002, '2002'), (2003, '2003'), (2004, '2004'), (2005, '2005'), (2006, '2006'), (2007, '2007'), (2008, '2008'), (2009, '2009'), (2010, '2010'), (2011, '2011'), (2012, '2012'), (2013, '2013'), (2014, '2014'), (2015, '2015'), (2016, '2016'), (2017, '2017'), (2018, '2018'), (2019, '2019'), (2020, '2020'), (2021, '2021'), (2022, '2022'), (2023, '2023')], default=2022)),
                ('year_to', models.IntegerField(choices=[(2000, '2000'), (2001, '2001'), (2002, '2002'), (2003, '2003'), (2004, '2004'), (2005, '2005'), (2006, '2006'), (2007, '2007'), (2008, '2008'), (2009, '2009'), (2010, '2010'), (2011, '2011'), (2012, '2012'), (2013, '2013'), (2014, '2014'), (2015, '2015'), (2016, '2016'), (2017, '2017'), (2018, '2018'), (2019, '2019'), (2020, '2020'), (2021, '2021'), (2022, '2022'), (2023, '2023')], default=2023)),
                ('assigned_faculty_member', models.ForeignKey(blank=True, limit_choices_to={'role__name': 'Faculty Member'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_member', to=settings.AUTH_USER_MODEL)),
                ('batch', modelcluster.fields.ParentalKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='department_batch_year', to='departments.batch')),
                ('collection', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='batch_year_collection', to='wagtailcore.collection')),
                ('students', models.ManyToManyField(blank=True, limit_choices_to={'role__name': 'Student'}, related_name='batch_year_students', to=settings.AUTH_USER_MODEL, verbose_name='batch_year_students')),
            ],
            options={
                'verbose_name': 'Batch Year',
                'verbose_name_plural': 'Batch Years',
                'unique_together': {('batch', 'year_from', 'year_to')},
            },
        ),
    ]
