from django.db.models import Subquery, OuterRef

from jcourse_api.models import *


def get_semesters():
    return Semester.objects.all()


def get_announcements():
    return Announcement.objects.filter(available=True)


def get_course_list_queryset(user: User):
    return Course.objects.select_related('main_teacher').prefetch_related('categories', 'department')


def get_search_course_queryset(q: str, user: User):
    courses = get_course_list_queryset(user)
    if q == '':
        return courses.none()
    courses = courses.filter(
        Q(code__icontains=q) | Q(name__icontains=q) | Q(main_teacher__name__icontains=q) |
        Q(main_teacher__pinyin__iexact=q) | Q(main_teacher__abbr_pinyin__icontains=q))
    return courses


def get_reviews(user: User):
    reviews = Review.objects.select_related('course', 'course__main_teacher', 'semester')
    if not user.is_authenticated:
        return reviews
    my_reaction = ReviewReaction.objects.filter(user=user, review_id=OuterRef('pk')).values('reaction')
    return reviews.annotate(my_reaction=Subquery(my_reaction[:1]))


def get_enrolled_courses(user: User):
    return EnrollCourse.objects.filter(user=user).values('semester_id', 'course_id')


def get_my_reviewed(user: User):
    return Review.objects.filter(user=user).values('course_id', 'semester_id', 'id')
