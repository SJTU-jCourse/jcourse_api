# Generated by Django 4.2.3 on 2023-08-11 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ad', '0002_alter_promotion_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='promotion',
            name='click_times',
            field=models.IntegerField(default=0, verbose_name='点击次数'),
        ),
    ]
