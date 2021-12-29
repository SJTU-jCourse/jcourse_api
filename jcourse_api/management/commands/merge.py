from django.core.management import BaseCommand

from jcourse_api.models import Course, Review, EnrollCourse, Teacher


class Command(BaseCommand):
    help = 'Merge courses'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--old', type=str)
        parser.add_argument('-n', '--new', type=str)
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--code', action="store_true", help='merge by code')
        group.add_argument('--cid', action="store_true", help='merge by course id')
        group.add_argument('--tid', action="store_true", help='merge by teacher id')

    def merge_course(self, old_course: Course, new_course: Course):
        reviews = Review.objects.filter(course=old_course)
        for review in reviews:
            review.course = new_course
            review.save()
        enrolls = EnrollCourse.objects.filter(course=old_course)
        for enroll in enrolls:
            if not EnrollCourse.objects.filter(user=enroll.user,
                                               semester=enroll.semester,
                                               course=new_course).exists():
                enroll.course = new_course
                enroll.save()
        old_course.delete()

    def merge_course_id(self, old_id, new_id):
        try:
            old_course = Course.objects.get(pk=old_id)
            new_course = Course.objects.get(pk=new_id)
            self.stdout.write(f'found old course {old_course}, new course {new_course}')
            self.merge_course(old_course, new_course)
            self.stdout.write(f'merged')
        except Course.DoesNotExist:
            return

    def merge_teacher(self, old_teacher, new_teacher):
        old_courses = Course.objects.filter(main_teacher=old_teacher)
        for course in old_courses:
            try:
                new_course = Course.objects.get(code=course.code, main_teacher=new_teacher)
                self.merge_course(course, new_course)
            except Course.DoesNotExist:
                course.main_teacher = new_teacher
                course.save()
        old_teacher.delete()

    def merge_teacher_id(self, old_id, new_id):
        try:
            old_teacher = Teacher.objects.get(pk=old_id)
            new_teacher = Teacher.objects.get(pk=new_id)
            self.stdout.write(f'found old teacher {old_teacher}, new teacher {new_teacher}')
            self.merge_teacher(old_teacher, new_teacher)
            self.stdout.write(f'merged')
        except Teacher.DoesNotExist:
            return

    def replace_code(self, old_code, new_code):
        try:
            courses = Course.objects.filter(code=old_code).prefetch_related('main_teacher')
            for course in courses:
                try:
                    new_code_course = Course.objects.get(code=new_code, main_teacher=course.main_teacher)
                    self.stdout.write(
                        f'merge code: {old_code}, {new_code}, {new_code_course.name}, {new_code_course.main_teacher.name}')
                    self.merge_course(course, new_code_course)
                except Course.DoesNotExist:
                    course.code = new_code
                    self.stdout.write(
                        f'replace code: {old_code}, {new_code}, {course.name}, {course.main_teacher.name}')
                    course.save()
                    continue
        except Course.DoesNotExist:
            return

    def handle(self, *args, **options):
        if options['old'] and options['new']:
            if options['code']:
                self.replace_code(options['old'], options['new'])
            elif options['cid']:
                self.merge_course_id(options['old'], options['new'])
            elif options['tid']:
                self.merge_teacher_id(options['old'], options['new'])
        else:
            self.stdout.write(f'No value provided!')
        self.stdout.write('Result: Replaced')
