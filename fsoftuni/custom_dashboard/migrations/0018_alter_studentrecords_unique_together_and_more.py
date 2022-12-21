# Generated by Django 4.0.5 on 2022-09-18 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('institutes', '0010_alter_institute_name'),
        ('custom_dashboard', '0017_alter_studentrecords_batch_year'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='studentrecords',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='studentrecords',
            name='level',
            field=models.IntegerField(choices=[(1, 'I'), (2, 'II'), (3, 'III'), (4, 'IV')], default=1),
        ),
        migrations.AlterUniqueTogether(
            name='studentrecords',
            unique_together={('institute', 'batch_year', 'term', 'level')},
        ),
    ]
