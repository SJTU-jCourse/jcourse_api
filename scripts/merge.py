from jcourse_api.models import Course, Review, FormerCode


def replace_code(old_code, new_code):
    try:
        courses = Course.objects.filter(code=old_code)
        for course in courses:
            # print(course.name, course.main_teacher)
            try:
                new_code_course = Course.objects.get(code=new_code, main_teacher=course.main_teacher)
                print(old_code, new_code, new_code_course.name, new_code_course.main_teacher.name)
                try:
                    reviews = Review.objects.filter(course=course)
                    for review in reviews:
                        review.course = new_code_course
                        review.save()
                except Review.DoesNotExist:
                    continue
                course.delete()
            except Course.DoesNotExist:
                course.code = new_code
                print(old_code, new_code, course.name, course.main_teacher.name)
                course.save()
                continue
    except Course.DoesNotExist:
        return


items = FormerCode.objects.all()
for item in items:
    replace_code(item.old_code, item.new_code)
