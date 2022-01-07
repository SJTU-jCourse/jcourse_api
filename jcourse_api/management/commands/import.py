from django.core.management import BaseCommand
from tablib import Dataset

from jcourse_api.admin import *


class Command(BaseCommand):
    help = 'Import from csv'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file', type=str, help='filename')
        parser.add_argument('-y', '--yes', action="store_true", help='no dry run')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-c', '--course', action="store_true", help='import courses')
        group.add_argument('-t', '--teacher', action="store_true", help='import teachers')

    def import_course(self, filename: str, dry_run: bool):
        course_resource = CourseResource()
        with open(filename, mode='r') as f:
            dataset = Dataset().load(f)
        result = course_resource.import_data(dataset, dry_run)
        self.stdout.write(f'{result.has_errors()}')

    def import_teacher(self, filename: str, dry_run: bool):
        teacher_resource = TeacherResource()
        with open(filename, mode='r') as f:
            dataset = Dataset().load(f)
        result = teacher_resource.import_data(dataset, dry_run)
        self.stdout.write(f'{result.has_errors()}')

    def handle(self, *args, **options):
        if options['file']:
            if options['course']:
                self.import_course(options['file'], not options['yes'])
            elif options['teacher']:
                self.import_teacher(options['file'], not options['yes'])
        else:
            self.stdout.write(f'No filename provided!')
