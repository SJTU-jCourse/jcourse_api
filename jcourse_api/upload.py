import csv
import io
import re
from django.core.files.uploadedfile import InMemoryUploadedFile
from pypinyin import pinyin, lazy_pinyin, Style
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from jcourse_api.serializers import *


def regulate_department(raw_name: str) -> str:  # 将系统一到学院层面
    if any(raw_name == x for x in ['软件学院', '微电子学院', '计算机科学与工程系']):
        return '电子信息与电气工程学院'
    if raw_name == '高分子科学与工程系':
        return '化学化工学院'
    return raw_name


def update_code():
    scripts_dir = './scripts'
    former_codes = dict()
    with open(f'{scripts_dir}/former_code.csv', mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            former_codes[row['old_code']] = row['new_code']
    return former_codes


def clean_data(csv_reader, data):
    new_codes = update_code()

    for line in csv_reader:
        tmp = line['教学班名称']
        semester = re.findall(r'\d{4}-\d{4}-\d', tmp)
        semester = ''.join(semester)
        if semester not in data.semesters and semester != '':
            data.semesters.append(semester)
        teacher_groups = line['合上教师']
        if teacher_groups == 'QT2002231068/THIERRY; Fine; VAN CHUNG/无[外国语学院]':
            teacher_groups = 'QT2002231068/THIERRY, Fine, VAN CHUNG/无[外国语学院]'

        teacher_groups = teacher_groups.split(';')
        tid_groups = []
        for teacher in teacher_groups:
            try:
                tid, name, title = teacher.split('/')
            except ValueError:
                print("\"" + teacher + "\"")
                continue
            department = regulate_department(title[title.find('[') + 1:-1])
            title = title[0:title.find('[')]
            my_pinyin = ''.join(lazy_pinyin(name))
            abbr_pinyin = ''.join([i[0] for i in pinyin(name, style=Style.FIRST_LETTER)])
            data.teachers.add((tid, name, title, department, my_pinyin, abbr_pinyin, semester))
            tid_groups.append(tid)
            title = teacher.split('/')[2]
            department = regulate_department(title[title.find('[') + 1:-1])
            data.departments.add(department)
        department = line['开课院系']
        if department == '研究生院':  # 跳过所有的研究生课程（主要原因是没有main_teacher字段）
            continue
        data.departments.add(department)
        name = line['课程名称']
        code = line['课程号']

        origin_categories = line['通识课归属模块'].split(',')
        course_categories = set()
        for origin_category in origin_categories:
            category = re.sub(u"\\(.*?\\)|（.*?）", "", origin_category)
            if category == "数学或逻辑学" or category == "自然科学与工程技术":
                continue
            if category == "" and department == '研究生院':
                category = '研究生'
                name = name.removesuffix('（研）')
            if category == "" and line['年级'] == "0":
                if line['课程号'].startswith('SP'):
                    category = '新生研讨'
                else:
                    category = '通选'
            if category == "" and any(code.startswith(x) for x in ['PE001C', 'PE002C', 'PE003C', 'PE004C']):
                category = '体育'
            data.categories.add(category)
            course_categories.add(category)
            if category == "" and code in new_codes:
                code = new_codes[code]
        main_teacher = line['任课教师'].split('|')[0] if line['任课教师'] else tid_groups[0]
        if department != '致远学院':
            data.course_department[(code, main_teacher)] = department
        # code	name	credit	department	category    main_teacher	teacher_group
        data.courses.add(
            (code, name, line['学分'], department, ';'.join(course_categories),
             main_teacher, ';'.join(tid_groups), semester))

    courses_filter = []
    for course in data.courses:
        other_dept = data.course_department.get((course[0], course[5]), '')
        if course[3] == '致远学院' and other_dept != '' and other_dept != '致远学院':
            print(course)
            continue
        if (course[0], course[5]) not in courses_filter:
            courses_filter.append((course[0], course[5]))
            data.unique_courses.add(course)

    return data


def get_id(name):
    if name == "semester":
        semester_id = {}
        semesters = list(Semester.objects.values_list('id', 'name'))
        for semester in semesters:
            semester_id[semester[1]] = semester[0]
        return semester_id
    elif name == "department":
        department_id = {}
        departments = list(Department.objects.values_list('id', 'name'))
        for department in departments:
            department_id[department[1]] = department[0]
        return department_id
    elif name == "category":
        category_id = {}
        categories = list(Category.objects.values_list('id', 'name'))
        for category in categories:
            category_id[category[1]] = category[0]
        return category_id
    elif name == "teacher":
        teacher_id = {}
        teachers = list(Teacher.objects.values_list('id', 'tid'))
        for teacher in teachers:
            teacher_id[teacher[1]] = teacher[0]
        return teacher_id
    elif name == "course":
        course_id = {}
        courses = list(Course.objects.values_list('id', 'code'))
        for course in courses:
            course_id[course[1]] = course[0]
        return course_id


def pre_import(data):
    to_be_created_d = []
    to_be_created_c = []

    try:
        Semester.objects.create(name=data.semesters[-1])
    except IntegrityError:
        pass

    for department in data.departments:
        d = Department(name=department)
        to_be_created_d.append(d)
    Department.objects.bulk_create(to_be_created_d, ignore_conflicts=True)

    for category in data.categories:
        c = Category(name=category)
        to_be_created_c.append(c)
    Category.objects.bulk_create(to_be_created_c, ignore_conflicts=True)


def import_dependent_data(data):
    to_be_created_t = []
    to_be_created_co = []
    department_id = get_id("department")
    semester_id = get_id("semester")
    category_id = get_id("category")

    for teacher in data.teachers:
        t = Teacher(tid=teacher[0], name=teacher[1], title=teacher[2],
                    department_id=department_id[teacher[3]],
                    pinyin=teacher[4], abbr_pinyin=teacher[5],
                    last_semester_id=semester_id[data.semesters[-1]])
        to_be_created_t.append(t)
    Teacher.objects.bulk_create(to_be_created_t, ignore_conflicts=True)

    teacher_id = get_id("teacher")
    for course in data.unique_courses:
        c = Course(code=course[0], name=course[1], credit=course[2],
                   department_id=department_id[course[3]],
                   main_teacher_id=teacher_id[course[5]],
                   last_semester_id=semester_id[data.semesters[-1]])
        to_be_created_co.append(c)
    Course.objects.bulk_create(to_be_created_co, ignore_conflicts=True)

    course_id = get_id("course")
    categories = []
    teacher_group = []
    for course in data.unique_courses:
        course_categories = course[4].split(';')
        for course_category in course_categories:
            course_category = Course.categories.through(course_id=course_id[course[0]],
                                                        category_id=category_id[course_category])
            categories.append(course_category)

        course_teachers = course[6].split(';')
        for course_teacher in course_teachers:
            course_teacher = Course.teacher_group.through(course_id=course_id[course[0]],
                                                          teacher_id=teacher_id[course_teacher])
            teacher_group.append(course_teacher)

    Course.categories.through.objects.bulk_create(categories, ignore_conflicts=True)
    Course.teacher_group.through.objects.bulk_create(teacher_group, ignore_conflicts=True)


class UploadData:
    semesters = []
    departments = set()
    categories = set()
    teachers = set()
    courses = set()
    unique_courses = set()
    course_department = dict()


class FileUploadView(APIView):
    parser_class = (FileUploadParser,)

    @staticmethod
    def post(request):
        if 'file' not in request.data:
            raise ParseError("Empty content")
        file: InMemoryUploadedFile = request.data['file']
        csv_reader = csv.DictReader(io.StringIO(file.read().decode('gbk')))
        all_data = UploadData
        cleaned_data = clean_data(csv_reader, all_data)
        pre_import(cleaned_data)
        import_dependent_data(cleaned_data)

        return Response(status=status.HTTP_201_CREATED)
