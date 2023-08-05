from rest_framework.decorators import api_view
from rest_framework.response import Response

from jcourse_api.repository import *
from jcourse_api.serializers import *


# one request for all common info (announcements, semesters, enrolled courses, reviewed courses, user)
@api_view(['GET'])
def get_common_info(request):
    user = request.user
    announcements = get_announcements()
    semesters = get_semesters()
    enrolled_courses = get_enrolled_courses(user)
    my_reviews = get_my_reviewed(user)

    return Response({"user": UserSerializer(user).data,
                     "announcements": AnnouncementSerializer(announcements, many=True).data,
                     "semesters": SemesterSerializer(semesters, many=True).data,
                     "enrolled_courses": enrolled_courses,
                     "my_reviews": my_reviews
                     })
