from django.core.management import BaseCommand
from django.db.models import Count, Q

from jcourse_api.models import Course


def get_duplicated():
    dups = Course.objects.values("main_teacher", "name", "credit").annotate(count=Count('id')).filter(count__gt=1)
    conditions = Q(pk=None)
    for dup in dups:
        conditions = conditions | Q(main_teacher=dup['main_teacher'], name=dup['name'], credit=dup['credit'])
    courses = Course.objects.filter(conditions).order_by("name", "main_teacher", "id")
    return courses


class Command(BaseCommand):
    help = 'Check duplicated courses'

    def handle(self, *args, **options):
        courses = get_duplicated().select_related("main_teacher")
        for course in courses:
            self.stdout.write(f"{course.code} {course.name} {course.main_teacher.name} {course.id}")
