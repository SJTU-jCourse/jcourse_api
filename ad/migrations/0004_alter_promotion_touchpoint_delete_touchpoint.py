# Generated by Django 4.2.4 on 2023-08-12 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ad', '0003_promotion_click_times'),
    ]

    operations = [
        migrations.AlterField(
            model_name='promotion',
            name='touchpoint',
            field=models.IntegerField(blank=True, choices=[(1, '更多课程下方')], db_index=True, null=True, verbose_name='触点'),
        ),
        migrations.DeleteModel(
            name='Touchpoint',
        ),
    ]
