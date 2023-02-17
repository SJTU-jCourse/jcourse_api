import csv
from typing import IO

from jcourse_api.models import Course


def export_courses_to_csv(f: IO):
    csv_writer = csv.writer(f)
    courses_output = []
    courses = Course.objects.all().prefetch_related('main_teacher')
    for course in courses:
        courses_output.append([course.code, course.name, course.main_teacher.name, course.pk])
    csv_writer.writerow(['code', 'name', 'main_teacher', 'id'])
    csv_writer.writerows(courses_output)
