# Generated by Django 4.0.3 on 2022-03-03 19:00
from django.contrib.auth.models import User
from django.db import migrations
from django.db.models import F

from jcourse_api.models import Review, UserPoint
from jcourse_api.utils.point import get_user_point_with_reviews
from jcourse_api.views import get_user_point


def get_old_point(user: User):
    reviews = Review.objects.filter(user=user)
    return get_user_point_with_reviews(user, reviews)


def make_up_old_point(apps, schema_editor):
    reviews = Review.objects.filter(disapprove_count__gt=F('approve_count') * 2)
    user_ids = reviews.order_by('user').distinct('user').values_list('user', flat=True)
    for user_id in user_ids:
        user = User.objects.get(pk=user_id)
        old_point, _ = get_old_point(user)
        new_point = get_user_point(user)
        value = old_point['points'] - new_point['points']
        UserPoint.objects.create(user=user, value=value, description='升级补偿')
        print(user, old_point, new_point)


class Migration(migrations.Migration):
    dependencies = [
        ('jcourse_api', '0021_semester_available'),
    ]

    operations = [
        migrations.RunPython(make_up_old_point),
    ]
