import csv

from utils.course_data_clean import UploadData

encoding = 'utf-8'
data_dir = '../data'
semester = '2025-2026-1'

f = open(f'{data_dir}/{semester}.csv', mode='r', encoding='utf-8-sig')
reader = csv.DictReader(f)

data = UploadData()
data.clean_data_for_jwc(reader, '.')

f.close()
teachers = data.get_teachers()
teachers.append_col([semester] * len(teachers), header='last_semester')
courses = data.get_courses()
courses.append_col([semester] * len(courses), header='last_semester')
print(len(teachers), len(data.departments), len(data.categories), len(courses))

with open(f'{data_dir}/Teachers.csv', mode='w', encoding=encoding, newline='') as f:
    f.writelines(teachers.export("csv"))

with open(f'{data_dir}/Categories.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['name'])
    writer.writerows([[category] for category in data.categories])

with open(f'{data_dir}/Departments.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['name'])
    writer.writerows([[department] for department in data.departments])

with open(f'{data_dir}/Courses.csv', mode='w', encoding=encoding, newline='') as f:
    f.writelines(courses.export("csv"))
