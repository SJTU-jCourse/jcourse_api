import csv

from django.core.management import BaseCommand

from jcourse_api.models import Course


class Command(BaseCommand):
    help = 'Export courses\' base information'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--output', type=str, help='output filename')
        parser.add_argument('-e', '--encoding', type=str, help='output encoding')

    def handle(self, *args, **options):
        courses = Course.objects.all().prefetch_related('main_teacher')
        if not options['output']:
            self.stderr.write('Error: Need to provide output filename')
            return

        with open(options['output'], mode='w', newline='') as f:
            csv_writer = csv.writer(f)
            courses_output = []
            for course in courses:
                courses_output.append([course.code, course.name, course.main_teacher.name, course.pk])
            csv_writer.writerow(['code', 'name', 'main_teacher', 'id'])
            csv_writer.writerows(courses_output)
