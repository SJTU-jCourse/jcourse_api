import csv

from pypinyin import pinyin, lazy_pinyin, Style

former_codes = dict()

with open('former_code.csv', mode='r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        former_codes[row['old_code']] = row['new_code']

departments = set()
teachers = set()
categories = set()
courses = set()
encoding = 'utf-8'
data_dir = '../data'

course_department = dict()
with open(f'{data_dir}/2021-2022-2.csv', mode='r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    for row in reader:
        teacher_groups = row['合上教师'].split(';')
        tid_groups = []
        for teacher in teacher_groups:
            try:
                tid, name, title = teacher.split('/')
            except ValueError:
                print("\"" + teacher + "\"")
                continue
            department = title[title.find('[') + 1:-1]
            title = title[0:title.find('[')]
            my_pinyin = ''.join(lazy_pinyin(name))
            abbr_pinyin = ''.join([i[0] for i in pinyin(name, style=Style.FIRST_LETTER)])
            teachers.add((tid, name, title, department, my_pinyin, abbr_pinyin))
            tid_groups.append(tid)
            departments.add(department)
        department = row['开课院系']
        if any(department == x for x in ['软件学院', '微电子学院', '计算机科学与工程系']):
            department = '电子信息与电气工程学院'
        departments.add(department)

        code = row['课程号']
        if code in former_codes:
            code = former_codes[code]
        main_teacher = row['任课教师'].split('|')[0] if row['任课教师'] else tid_groups[0]
        if department != '致远学院':
            course_department[(code, main_teacher)] = department
        category = row['通识课归属模块'].split(',')[0]
        if category == "" and row['年级'] == "0":
            if row['课程号'].startswith('SP'):
                category = '新生研讨'
            elif any(x in row['选课备注'] for x in ['重修班', '不及格', '面向民族生', '面向留学生']):
                category = ''
            else:
                category = '通选'
        categories.add(category)
        # code	name	credit	department	category    main_teacher	teacher_group
        courses.add(
            (code, row['课程名称'], row['学分'], department, category,
             main_teacher, ';'.join(tid_groups)))

unique_courses = set()
for course in courses:
    if course[3] == '致远学院' and course_department.get((course[0], course[5]), '') != '致远学院':
        continue
    unique_courses.add(course)

print(len(teachers), len(departments), len(categories), len(courses))

with open(f'{data_dir}/Teachers.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['tid', 'name', 'title', 'department', 'pinyin', 'abbr_pinyin'])
    writer.writerows(teachers)

with open(f'{data_dir}/Categories.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['name'])
    writer.writerows([[category] for category in categories])

with open(f'{data_dir}/Departments.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['name'])
    writer.writerows([[department] for department in departments])

with open(f'{data_dir}/Courses.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['code', 'name', 'credit', 'department', 'category', 'main_teacher', 'teacher_group'])
    writer.writerows(unique_courses)
