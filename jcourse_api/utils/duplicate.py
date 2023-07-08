import re

from django.db.models import Count, Q

from jcourse_api.models import Teacher
from jcourse_api.utils import merge_teacher


def find_duplicated_teachers():
    dup = Teacher.objects.select_related("department").values("name", "department__name").annotate(
        count=Count("id")).filter(count__gt=1)
    q = Q()
    for d in dup:
        q = q | Q(name=d["name"], department__name=d["department__name"])
    candidates = Teacher.objects.select_related("department", "last_semester").filter(q)
    result = dict()
    for candidate in candidates:
        k = (candidate.name, candidate.department.name)
        v = (candidate, candidate.last_semester.name if candidate.last_semester else "2019-2020-1")
        if k in result:
            ex_v = result[k]
            if ex_v[1] > v[1]:  # 存在且学期更新
                continue
        result[k] = v
    return result, candidates


def check_tid(tid: str) -> bool:
    reg = re.compile("^[0-9]{5}$")
    return reg.match(tid) is None


def merge_duplicated_teachers():
    result, candidates = find_duplicated_teachers()
    for candidate in candidates:
        target = result[(candidate.name, candidate.department.name)][0]
        if target.id != candidate.id \
                and target.last_semester != candidate.last_semester \
                and check_tid(candidate.tid):
            print(candidate.name, candidate.tid, candidate.last_semester, target, target.tid, target.last_semester)
            merge_teacher(candidate, target)
