# Generated by Django 5.2.1 on 2025-05-26 11:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jcourse_api', '0042_no_point_by_review'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reviewrevision',
            name='review',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='jcourse_api.review', verbose_name='点评'),
        ),
    ]
