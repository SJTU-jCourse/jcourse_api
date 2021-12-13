import csv

from django.core.management import BaseCommand

from jcourse_api.models import Course, Review, FormerCode


class Command(BaseCommand):
    help = 'Merge courses by code'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--old', type=str, help='old code')
        parser.add_argument('-n', '--new', type=str, help='new code')
        parser.add_argument('-f', '--file', type=str, help='replace file')

    def replace_code(self, old_code, new_code):
        try:
            courses = Course.objects.filter(code=old_code).prefetch_related('main_teacher')
            for course in courses:
                try:
                    new_code_course = Course.objects.get(code=new_code, main_teacher=course.main_teacher)
                    self.stdout.write(
                        f'{old_code}, {new_code}, {new_code_course.name}, {new_code_course.main_teacher.name}')
                    try:
                        reviews = Review.objects.filter(course=course)
                        for review in reviews:
                            review.course = new_code_course
                            review.save()
                    except Review.DoesNotExist:
                        continue
                    course.delete()
                except Course.DoesNotExist:
                    course.code = new_code
                    self.stdout.write(f'{old_code}, {new_code}, {course.name}, {course.main_teacher.name}')
                    course.save()
                    continue
        except Course.DoesNotExist:
            return

    def handle(self, *args, **options):
        if options['file']:
            with open(options['file'], mode='r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.replace_code(row['old'], row['new'])
            self.stdout.write('Result: Replaced from file')
        else:
            if options['old'] and options['new']:
                self.replace_code(options['old'], options['new'])
            self.stdout.write('Result: Replaced')
