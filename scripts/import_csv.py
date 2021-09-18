import csv

from pypinyin import pinyin, lazy_pinyin, Style

former_codes = dict()

with open('../data/former_code.csv', mode='r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        former_codes[row['old_code']] = row['new_code']

languages = set()
departments = set()
teachers = set()
categories = set()
courses = set()
encoding = 'utf-8'
with open('../data/2021-2022-1.csv', mode='r', encoding='utf-8-sig') as f:
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
        departments.add(row['开课院系'])
        code = row['课程号']
        if code in former_codes:
            code = former_codes[code]
        category = row['通识课归属模块'].split(',')[0]
        if category == "" and row['年级'] == "0":
            if row['课程号'].startswith('SP'):
                category = '新生研讨'
            elif '重修班' in row['选课备注'] or '不及格' in row['选课备注']:
                category = ''
            else:
                category = '通选'
        categories.add(category)
        languages.add(row['授课语言'])
        # code	name	credit	department	category	language	main_teacher	teacher_group
        courses.add(
            (code, row['课程名称'], row['学分'], row['开课院系'], category,
             row['授课语言'], row['任课教师'].split('|')[0], ';'.join(tid_groups)))

print(len(teachers), len(departments), len(categories), len(languages), len(courses))

with open('../data/Teachers.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['tid', 'name', 'title', 'department', 'pinyin', 'abbr_pinyin'])
    writer.writerows(teachers)

with open('../data/Categories.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['name'])
    writer.writerows([[category] for category in categories])

with open('../data/Languages.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['name'])
    writer.writerows([[language] for language in languages])

with open('../data/Departments.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['name'])
    writer.writerows([[department] for department in departments])

with open('../data/Courses.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['code', 'name', 'credit', 'department', 'category', 'language', 'main_teacher', 'teacher_group'])
    writer.writerows(courses)
