# Generated by Django 4.0.8 on 2022-11-04 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_alter_customuser_batch'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnlineUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True)),
                ('users', models.JSONField(blank=True, default={}, null=True)),
            ],
        ),
    ]
