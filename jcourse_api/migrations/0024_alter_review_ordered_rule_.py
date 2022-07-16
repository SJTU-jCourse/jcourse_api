# Generated by Django 4.0.6 on 2022-07-16 09:19

from django.db import migrations


def create_modified_time(apps, schema_editor):
    Review = apps.get_model('jcourse_api', 'Review')
    for review in Review.objects.filter(modified=None):
        created_time = review.created
        review.modified = created_time
        review.save()


class Migration(migrations.Migration):
    dependencies = [
        ('jcourse_api', '0023_notice_url'),
    ]

    operations = [
        migrations.RunPython(create_modified_time),
        migrations.AlterModelOptions(
            name='review',
            options={'ordering': ['-modified'], 'verbose_name': '点评', 'verbose_name_plural': '点评'},
        ),
    ]
