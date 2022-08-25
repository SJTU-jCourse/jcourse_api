import csv
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
from pypinyin import pinyin, lazy_pinyin, Style
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from jcourse_api.serializers import *


def regulate_department(raw: str) -> str:  # 将系统一到学院层面
    if any(raw == x for x in ['软件学院', '微电子学院', '计算机科学与工程系']):
        return '电子信息与电气工程学院'
    if raw == '高分子科学与工程系':
        return '化学化工学院'
    return raw


def get_former_codes() -> dict[str, str]:
    scripts_dir = './scripts'
    former_codes: dict[str, str] = dict()
    with open(f'{scripts_dir}/former_code.csv', mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            former_codes[row['old_code']] = row['new_code']
    return former_codes


def regulate_categories(line: dict[str, str]) -> set[str]:
    origin_categories: list[str] = line['通识课归属模块'].split(',')
    categories: set[str] = set()
    code = line['课程号']
    department = line['开课院系']

    for origin_category in origin_categories:
        category = origin_category.removesuffix("（致远）")
        if category == "数学或逻辑学" or category == "自然科学与工程技术":
            continue
        if category != "":
            categories.add(category)

    if len(categories) == 0 and department == '研究生院':
        categories.add('研究生')
    if len(categories) == 0 and line['年级'] == "0":
        if line['课程号'].startswith('SP'):
            categories.add('新生研讨')
        else:
            categories.add('通选')
    if len(categories) == 0 and any(code.startswith(x) for x in ['PE001C', 'PE002C', 'PE003C', 'PE004C']):
        categories.add('体育')

    return categories


class UploadData:
    departments: set[str] = set()
    categories: set[str] = set()
    teachers: set[tuple] = set()
    courses: set[tuple] = set()
    unique_courses: set[tuple] = set()
    course_department: dict[tuple[str, str], str] = dict()


def deal_with_honor_courses(data: UploadData):
    for course in data.courses:
        other_dept = data.course_department.get((course[0], course[5]), '')  # code, tid
        if course[3] == '致远学院' and other_dept != '' and other_dept != '致远学院':
            continue
        data.unique_courses.add(course)


def deal_with_teacher_group(line: dict[str, str], data: UploadData) -> list[str]:
    teacher_group = line['合上教师']
    if teacher_group == 'QT2002231068/THIERRY; Fine; VAN CHUNG/无[外国语学院]':
        teacher_group = 'QT2002231068/THIERRY, Fine, VAN CHUNG/无[外国语学院]'
    teacher_group = teacher_group.split(';')
    ids: list[str] = []
    for teacher in teacher_group:
        try:
            tid, name, title = teacher.split('/')
        except ValueError:
            continue
        department = regulate_department(title[title.find('[') + 1:-1])
        title = title[0:title.find('[')]
        name_pinyin = ''.join(lazy_pinyin(name))
        abbr_pinyin = ''.join([i[0] for i in pinyin(name, style=Style.FIRST_LETTER)])
        data.teachers.add((tid, name, title, department, name_pinyin, abbr_pinyin))
        ids.append(tid)
        data.departments.add(department)
    return ids


def clean_data(csv_reader, data: UploadData):
    new_codes = get_former_codes()

    for line in csv_reader:
        print(line)
        teacher_ids = deal_with_teacher_group(line, data)
        department = line['开课院系']
        if department == '研究生院':  # 跳过所有的研究生课程（主要原因是没有main_teacher字段）
            continue
        data.departments.add(department)
        categories = regulate_categories(line)
        for category in categories:
            data.categories.add(category)

        name = line['课程名称']
        code = line['课程号']
        if len(categories) == 0 and code in new_codes:
            code = new_codes[code]
        main_teacher = line['任课教师'].split('|')[0] if line['任课教师'] else teacher_ids[0]

        if department != '致远学院':
            # 有些课程，显示致远学院和非致远学院同时开课，实际上是同一门课，这里取非致远
            data.course_department[(code, main_teacher)] = department
        # code	name	credit	department	category    main_teacher	teacher_group
        data.courses.add(
            (code, name, line['学分'], department, ";".join(categories),
             main_teacher, ";".join(teacher_ids)))

    deal_with_honor_courses(data)


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
    for course in data.unique_courses:
        c = Course(code=course[0], name=course[1], credit=course[2],
                   department_id=department_id[course[3]],
                   main_teacher_id=teacher_id[course[5]],
                   last_semester=semester)
        courses.append(c)
    created_courses = Course.objects.bulk_create(courses, ignore_conflicts=True)

    course_id = get_id_mapping("course")
    categories = []
    teacher_group = []
    for course in data.unique_courses:
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
    # permission_classes = [IsAdminUser]
    parser_class = (FileUploadParser,)

    @staticmethod
    def post(request):
        print(1)
        if 'file' not in request.data:
            raise ParseError("Empty content")
        file: InMemoryUploadedFile = request.data['file']
        semester: str = request.data['semester']
        print(semester)
        csv_reader = csv.DictReader(io.StringIO(file.read().decode('utf-8-sig')))
        data = UploadData()
        clean_data(csv_reader, data)
        pre_import(data)
        created_courses, created_teachers = import_dependent_data(data, semester)
        resp = {"courses": len(created_courses), "teachers": len(created_teachers)}
        return Response(resp, status=status.HTTP_201_CREATED)
