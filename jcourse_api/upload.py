import csv
import io

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import status
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from jcourse_api.serializers import *
from utils.course_data_clean import UploadData


def get_id_mapping(name: str) -> dict[str, int]:
    if name == "department":
        department_id = {}
        departments = Department.objects.values_list('id', 'name')
        for department in departments:
            department_id[department[1]] = department[0]
        return department_id
    elif name == "category":
        category_id = {}
        categories = Category.objects.values_list('id', 'name')
        for category in categories:
            category_id[category[1]] = category[0]
        return category_id
    elif name == "teacher":
        teacher_id = {}
        teachers = Teacher.objects.values_list('id', 'tid')
        for teacher in teachers:
            teacher_id[teacher[1]] = teacher[0]
        return teacher_id
    elif name == "course":
        course_id = {}
        courses = Course.objects.values_list('id', 'code')
        for course in courses:
            course_id[course[1]] = course[0]
        return course_id


def pre_import(data):
    departments: list[Department] = []
    categories: list[Category] = []

    for department in data.departments:
        d = Department(name=department)
        departments.append(d)
    Department.objects.bulk_create(departments, ignore_conflicts=True)

    for category in data.categories:
        c = Category(name=category)
        categories.append(c)
    Category.objects.bulk_create(categories, ignore_conflicts=True)


def import_dependent_data(data, semester: str):
    teachers = []
    courses = []
    department_id = get_id_mapping("department")
    semester, _ = Semester.objects.get_or_create(name=semester)
    category_id = get_id_mapping("category")

    for teacher in data.teachers:
        t = Teacher(tid=teacher[0], name=teacher[1], title=teacher[2],
                    department_id=department_id[teacher[3]],
                    pinyin=teacher[4], abbr_pinyin=teacher[5],
                    last_semester=semester)
        teachers.append(t)
    created_teachers = Teacher.objects.bulk_create(teachers, ignore_conflicts=True)

    teacher_id = get_id_mapping("teacher")
    for course in data.courses:
        c = Course(code=course[0], name=course[1], credit=course[2],
                   department_id=department_id[course[3]],
                   main_teacher_id=teacher_id[course[5]],
                   last_semester=semester)
        courses.append(c)
    created_courses = Course.objects.bulk_create(courses, ignore_conflicts=True)

    course_id = get_id_mapping("course")
    categories = []
    teacher_group = []
    for course in data.courses:
        course_categories: str = course[4]
        if course_categories != "":
            for course_category in course_categories.split(";"):
                course_category = Course.categories.through(course_id=course_id[course[0]],
                                                            category_id=category_id[course_category])
                categories.append(course_category)

        course_teachers: str = course[6]
        for course_teacher in course_teachers.split(";"):
            course_teacher = Course.teacher_group.through(course_id=course_id[course[0]],
                                                          teacher_id=teacher_id[course_teacher])
            teacher_group.append(course_teacher)

    Course.categories.through.objects.bulk_create(categories, ignore_conflicts=True)
    Course.teacher_group.through.objects.bulk_create(teacher_group, ignore_conflicts=True)

    return created_courses, created_teachers


class FileUploadView(APIView):
    permission_classes = [IsAdminUser]
    parser_class = (FileUploadParser,)

    @staticmethod
    def post(request):
        if 'file' not in request.data or 'semester' not in request.data:
            return Response({"details": "Bad arguments"}, status=status.HTTP_400_BAD_REQUEST)
        file: InMemoryUploadedFile = request.data['file']
        semester: str = request.data['semester']
        csv_reader = csv.DictReader(io.StringIO(file.read().decode('utf-8-sig')))
        data = UploadData()
        data.clean_data_for_jwc(csv_reader, './script')
        pre_import(data)
        created_courses, created_teachers = import_dependent_data(data, semester)
        resp = {"courses": len(created_courses), "teachers": len(created_teachers)}
        return Response(resp, status=status.HTTP_201_CREATED)
