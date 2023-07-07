from jcourse_api.models import *


def create_test_env() -> None:
    dept_seiee = Department.objects.create(name='SEIEE')
    dept_phy = Department.objects.create(name='PHYSICS')
    teacher_gao = Teacher.objects.create(tid=1, name='高女士', department=dept_seiee, title='教授',
                                         pinyin='gaoxiaofeng',
                                         abbr_pinyin='gxf')
    teacher_pan = Teacher.objects.create(tid=4, name='潘老师', department=dept_seiee, title='教授', pinyin='panli',
                                         abbr_pinyin='pl')
    teacher_liang = Teacher.objects.create(tid=2, name='梁女士', department=dept_phy, pinyin='liangqin',
                                           abbr_pinyin='lq')
    teacher_zhao = Teacher.objects.create(tid=3, name='赵先生', department=dept_phy, title='讲师', pinyin='zhaohao',
                                          abbr_pinyin='zh')
    category = Category.objects.create(name='通识')
    c1 = Course.objects.create(code='CS2500', name='算法与复杂性', credit=2, department=dept_seiee,
                               main_teacher=teacher_gao)
    c1.teacher_group.add(teacher_gao)
    c2 = Course.objects.create(code='CS1500', name='计算机科学导论', credit=4, department=dept_seiee,
                               main_teacher=teacher_gao)
    c2.teacher_group.add(teacher_gao)
    c2.teacher_group.add(teacher_pan)
    c3 = Course.objects.create(code='MARX1001', name='思想道德修养与法律基础', credit=3, department=dept_phy,
                               main_teacher=teacher_liang)
    c3.categories.add(category)
    c3.teacher_group.add(teacher_liang)
    c4 = Course.objects.create(code='MARX1001', name='思想道德修养与法律基础', credit=3, department=dept_phy,
                               main_teacher=teacher_zhao)
    c4.teacher_group.add(teacher_zhao)
    c4.categories.add(category)

    Semester.objects.create(name='2021-2022-1')
    Semester.objects.create(name='2021-2022-2')
    Semester.objects.create(name='2021-2022-3')
    Semester.objects.create(name='2022-2023-1', available=False)
    User.objects.create(username='test')


def create_review(username: str = 'test', code: str = 'CS1500', rating: int = 3) -> Review:
    user, _ = User.objects.get_or_create(username=username)
    course = Course.objects.filter(code=code).first()
    now = timezone.now()
    review = Review.objects.create(user=user, course=course, comment='TEST', rating=rating, score='W',
                                   semester=Semester.objects.get(name='2021-2022-1'),
                                   created_at=now, modified_at=now)
    ReviewReaction.objects.create(review=review, user=user, reaction=1)
    return review
