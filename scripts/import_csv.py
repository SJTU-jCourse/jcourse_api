import csv

import tablib

from utils.course_data_clean import UploadData

encoding = 'utf-8'
data_dir = '../data'
semester = '2025-2026-2'

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

chunk_size = 1000


def export_chunks(dataset, path_prefix):
    for i, start in enumerate(range(0, len(dataset), chunk_size), 1):
        chunk = tablib.Dataset(headers=dataset.headers)
        for row in dataset[start:start + chunk_size]:
            chunk.append(row)
        with open(f'{path_prefix}_{i}.csv', mode='w', encoding=encoding, newline='') as f:
            f.writelines(chunk.export("csv"))


export_chunks(teachers, f'{data_dir}/Teachers')

with open(f'{data_dir}/Categories.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['name'])
    writer.writerows([[category] for category in data.categories])

with open(f'{data_dir}/Departments.csv', mode='w', encoding=encoding, newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['name'])
    writer.writerows([[department] for department in data.departments])

export_chunks(courses, f'{data_dir}/Courses')
