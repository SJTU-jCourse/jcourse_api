from typing import Callable

from jcourse_api.models import *


def merge_course(old_course: Course, new_course: Course) -> bool:
    if old_course == new_course:
        return False
    reviews = Review.objects.filter(course=old_course)
    reviews.update(course=new_course)
    update_course_reviews(new_course)
    # 查询同时选了两门课的用户，删除旧记录
    new_enrolls = EnrollCourse.objects.filter(course=new_course).values('user')
    common = EnrollCourse.objects.filter(user__in=new_enrolls, course=old_course)
    if common.exists():
        common.delete()
    # 更新记录
    EnrollCourse.objects.filter(course=old_course).update(course=new_course)
    old_course.delete()
    return True


def merge_course_by_id(old_id: int, new_id: int, pre_func: Callable[[Course, Course], None] = None) -> bool:
    if old_id == new_id:
        return False
    try:
        old_course = Course.objects.get(pk=old_id)
        new_course = Course.objects.get(pk=new_id)
        if pre_func:
            pre_func(old_course, new_course)
        return merge_course(old_course, new_course)
    except Course.DoesNotExist:
        return False


def replace_course_code_multi(old_code: str, new_code: str,
                              pre_merge: Callable[[Course, Course], None] = None,
                              pre_replace: Callable[[Course], None] = None):
    if old_code == new_code:
        return
    courses = Course.objects.filter(code=old_code).prefetch_related('main_teacher')
    for course in courses:
        try:
            new_code_course = Course.objects.get(code=new_code, main_teacher=course.main_teacher)
            if pre_merge:
                pre_merge(course, new_code_course)
            merge_course(course, new_code_course)
        except Course.DoesNotExist:
            if pre_replace:
                pre_replace(course)
            course.code = new_code
            course.save()
            continue


def merge_teacher(old_teacher: Teacher, new_teacher: Teacher) -> bool:
    if old_teacher == new_teacher:
        return False
    old_courses = Course.objects.filter(main_teacher=old_teacher)
    for course in old_courses:
        try:
            new_course = Course.objects.get(code=course.code, main_teacher=new_teacher)
            merge_course(course, new_course)
        except Course.DoesNotExist:
            course.main_teacher = new_teacher
            course.save()
    old_teacher.delete()
    return True


def merge_teacher_by_id(old_id: int, new_id: int,
                        pre_func: Callable[[Teacher, Teacher], None] = None) -> bool:
    if old_id == new_id:
        return False
    try:
        old_teacher = Teacher.objects.get(pk=old_id)
        new_teacher = Teacher.objects.get(pk=new_id)
        if pre_func:
            pre_func(old_teacher, new_teacher)
        merge_teacher(old_teacher, new_teacher)
        return True
    except Teacher.DoesNotExist:
        return False
