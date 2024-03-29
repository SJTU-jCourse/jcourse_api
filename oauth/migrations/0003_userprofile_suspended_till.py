# Generated by Django 4.2.3 on 2023-08-05 09:02
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import migrations, models

from utils.common import get_time_now


def add_suspended_till(apps, schema_editor):
    UserProfile = apps.get_model('oauth', 'UserProfile')
    suspended_user_ids = User.objects.filter(is_active=False, is_staff=False).values_list('id', flat=True)
    suspended_till = get_time_now() + timedelta(days=90)
    UserProfile.objects.filter(user_id__in=suspended_user_ids).update(suspended_till=suspended_till)


class Migration(migrations.Migration):
    dependencies = [
        ('oauth', '0002_userprofile_lowercase'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='suspended_till',
            field=models.DateTimeField(db_index=True, default=None, blank=True, null=True, verbose_name='封禁到'),
        ),
        migrations.RunPython(add_suspended_till, reverse_code=migrations.RunPython.noop)
    ]
