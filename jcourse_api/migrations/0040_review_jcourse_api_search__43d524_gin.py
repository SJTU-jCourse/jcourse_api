# Generated by Django 4.2.4 on 2023-08-12 13:50

import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jcourse_api', '0039_review_search_vector'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='review',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_vector'], name='jcourse_api_search__43d524_gin'),
        ),
    ]