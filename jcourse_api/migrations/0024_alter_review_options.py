# Generated by Django 4.0.6 on 2022-07-16 09:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jcourse_api', '0023_notice_url'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='review',
            options={'ordering': ['-modified'], 'verbose_name': '点评', 'verbose_name_plural': '点评'},
        ),
    ]
