import csv

from django.core.management import BaseCommand

from jcourse_api.models import *


class Command(BaseCommand):
    help = 'Update semester from csv. Run this by semester desc.'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file', type=str, help='filename')
        parser.add_argument('-s', '--semester', type=str, help='semester name')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-c', '--course', action="store_true", help='import courses')
        group.add_argument('-t', '--teacher', action="store_true", help='import teachers')

    def update_course(self, filename: str, semester_name: str):
        semester = Semester.objects.get(name=semester_name)
        with open(filename, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                course = Course.objects.filter(last_semester=None, code=row['code'],
                                               main_teacher__tid=row['main_teacher'])
                if course.exists():
                    course = course.get()
                    course.last_semester = semester
                    print(course)
                    course.save()

    def update_teacher(self, filename: str, semester_name: str):
        semester = Semester.objects.get(name=semester_name)
        with open(filename, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                teacher = Teacher.objects.filter(last_semester=None, tid=row['tid'])
                if teacher.exists():
                    teacher = teacher.get()
                    teacher.last_semester = semester
                    print(teacher)
                    teacher.save()

    def handle(self, *args, **options):
        if options['file'] and options['semester']:
            if options['course']:
                self.update_course(options['file'], options['semester'])
            elif options['teacher']:
                self.update_teacher(options['file'], options['semester'])
        else:
            self.stdout.write(f'No filename provided!')
