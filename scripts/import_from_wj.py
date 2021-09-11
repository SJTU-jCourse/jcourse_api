import csv

from django.contrib.auth.models import User

from jcourse_api.models import Course, Review, FormerCode, Semester

f = open('./data/2021_wenjuan.csv', mode='r', encoding='utf-8-sig')
csv_reader = csv.DictReader(f)
q = []
users = User.objects.filter(username__istartswith='工具人')
for row in csv_reader:
    try:
        code, course_name, teacher = row['课程'].split(' ')
        # print(code, course_name, teahcer)
        try:
            codes = [code]
            try:
                former_code = FormerCode.objects.get(old_code=code).new_code
                codes.append(former_code)
            except FormerCode.DoesNotExist:
                pass
            course = Course.objects.get(code__in=codes, main_teacher__name=teacher)
            has_reviewed = Review.objects.filter(course=course, user__in=users).exists()
            if not has_reviewed:
                q.append((course, row))
                print(course)
        except Course.DoesNotExist:
            print("未查到：", code, course_name, teacher)
    except ValueError:
        # print(row['课程'])
        pass
i = 1
while len(q) > 0:
    new_q = []
    user, _ = User.objects.get_or_create(username=f"工具人{i}号")
    for course, row in q:
        if Review.objects.filter(course=course, user=user).exists():
            new_q.append((course, row))
            continue
        year = int(row['学期'][0:4])
        term = row['学期'][-1]
        if term == '春':
            semester = Semester.objects.get(name=f'{year - 1}-{year}-2')
        elif term == '夏':
            semester = Semester.objects.get(name=f'{year - 1}-{year}-3')
        else:
            semester = Semester.objects.get(name=f'{year}-{year + 1}-1')
        comment = f"课程内容：{row['课程内容']}\n上课自由度：{row['课程自由度']}\n考核标准：{row['考核标准']}\n教师：{row['教师']}"
        rating = int(row['安利程度']) // 2
        review = Review(course=course, user=user, comment=comment, rating=rating, semester=semester, score=row['成绩'])
        review.save()
        # print(review)
    q = new_q
    i = i + 1
