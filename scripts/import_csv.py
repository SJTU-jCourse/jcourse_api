import csv

from pypinyin import pinyin, lazy_pinyin, Style

languages = set()
departments = set()
teachers = set()
categories = set()
courses = set()
encoding = 'utf-8'
f = open('../data/2021-2022-1-0.csv', mode='r', encoding='utf-8-sig')
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

    category = row['通识课归属模块'].split(',')[0]
    if category == "" and row['年级'] == "0":
        if row['课程号'].startswith('SP'):
            category = '新生研讨'
        else:
            category = '通选'
    categories.add(category)
    languages.add(row['授课语言'])
    # code	name	credit	department	category	language	main_teacher	teacher_group
    courses.add(
        (row['课程号'], row['课程名称'], row['学分'], row['开课院系'], category,
         row['授课语言'], row['任课教师'].split('|')[0], ';'.join(tid_groups)))
f.close()

print(len(teachers), len(departments), len(categories), len(languages), len(courses))

f = open('../data/Teachers.csv', mode='w', encoding=encoding, newline='')
writer = csv.writer(f)
writer.writerow(['tid', 'name', 'title', 'department', 'pinyin', 'abbr_pinyin'])
writer.writerows(teachers)
f.close()

f = open('../data/Categories.csv', mode='w', encoding=encoding, newline='')
writer = csv.writer(f)
writer.writerow(['name'])
writer.writerows([[category] for category in categories])
f.close()

f = open('../data/languages.csv', mode='w', encoding=encoding, newline='')
writer = csv.writer(f)
writer.writerow(['name'])
writer.writerows([[language] for language in languages])
f.close()

f = open('../data/departments.csv', mode='w', encoding=encoding, newline='')
writer = csv.writer(f)
writer.writerow(['name'])
writer.writerows([[department] for department in departments])
f.close()

f = open('../data/courses.csv', mode='w', encoding=encoding, newline='')
writer = csv.writer(f)
writer.writerow(['code', 'name', 'credit', 'department', 'category', 'language', 'main_teacher', 'teacher_group'])
writer.writerows(courses)
f.close()
