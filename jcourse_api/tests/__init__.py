from jcourse_api.models import *


def create_test_env() -> None:
    dept_seiee = Department.objects.create(pk=1, name='SEIEE')
    dept_phy = Department.objects.create(pk=2, name='PHYSICS')
    teacher_gao = Teacher.objects.create(tid=1, name='高女士', department=dept_seiee, title='教授', pinyin='gaoxiaofeng',
                                         abbr_pinyin='gxf')
    teacher_pan = Teacher.objects.create(tid=4, name='潘老师', department=dept_seiee, title='教授', pinyin='panli',
                                         abbr_pinyin='pl')
    teacher_liang = Teacher.objects.create(tid=2, name='梁女士', department=dept_phy, pinyin='liangqin', abbr_pinyin='lq')
    teacher_zhao = Teacher.objects.create(tid=3, name='赵先生', department=dept_phy, title='讲师', pinyin='zhaohao',
                                          abbr_pinyin='zh')
    category = Category.objects.create(pk=1, name='通识')
    chinese = Language.objects.create(pk=1, name='中文')
    bilingual = Language.objects.create(pk=2, name='双语')
    c1 = Course.objects.create(pk=1, code='CS2500', name='算法与复杂性', credit=2, department=dept_seiee,
                               main_teacher=teacher_gao,
                               language=bilingual)
    c1.teacher_group.add(teacher_gao)
    c2 = Course.objects.create(pk=2, code='CS1500', name='计算机科学导论', credit=4, department=dept_seiee,
                               main_teacher=teacher_gao,
                               language=bilingual)
    c2.teacher_group.add(teacher_gao)
    c2.teacher_group.add(teacher_pan)
    c3 = Course.objects.create(pk=3, code='MARX1001', name='思想道德修养与法律基础', credit=3, department=dept_phy,
                               main_teacher=teacher_liang, category=category, language=chinese)
    c3.teacher_group.add(teacher_liang)
    c4 = Course.objects.create(pk=4, code='MARX1001', name='思想道德修养与法律基础', credit=3, department=dept_phy,
                               main_teacher=teacher_zhao, category=category, language=chinese)
    c4.teacher_group.add(teacher_zhao)
    FormerCode.objects.create(old_code='CS250', new_code='CS2500')
    FormerCode.objects.create(old_code='CS251', new_code='CS2500')
    FormerCode.objects.create(old_code='CS150', new_code='CS1500')
    FormerCode.objects.create(old_code='TH000', new_code='MARX1001')
    Semester.objects.create(pk=1, name='2021-2022-1')
    Semester.objects.create(pk=2, name='2021-2022-2')
    Semester.objects.create(pk=3, name='2021-2022-3')
    User.objects.create(username='test')


def create_review(username: str = 'test', code: str = 'CS1500', rating: int = 3) -> Review:
    user, _ = User.objects.get_or_create(username=username)
    course = Course.objects.get(code=code)
    review = Review.objects.create(user=user, course=course, comment='TEST', rating=rating, score='W', semester_id=1)
    Action.objects.create(review=review, user=user, action=1)
    return review
