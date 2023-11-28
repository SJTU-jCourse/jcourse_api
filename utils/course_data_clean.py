import csv
import re

import tablib
from pypinyin import pinyin, lazy_pinyin, Style


# 教学信息服务网数据的处理，将系统一到学院层面
def regulate_department(raw: str) -> str:
    if any(raw == x for x in
           ['软件学院', '微电子学院', '计算机科学与工程系', '电子工程系', '微电子与纳米科学系', '信息安全工程学院']):
        return '电子信息与电气工程学院'
    if any(raw == x for x in
           ['高分子科学与工程系', '化学工程系']):
        return '化学化工学院'
    if any(raw == x for x in
           ['机电控制与物流装备研究所', '汽车工程研究院', '重大装备设计与控制研究所']):
        return '机械与动力工程学院'
    if any(raw == x for x in
           ['植物科学系', '新农村发展研究院', '资源与环境系']):
        return '农业与生物学院'
    if raw == '原子分子与等离子体物理研究所':
        return '物理与天文学院'
    if raw == '土木工程系':
        return '船舶海洋与建筑工程学院'
    if raw == '设计系':
        return '设计学院'
    if raw == '公共管理系':
        return '国际与公共事务学院'
    if raw == '历史系':
        return '人文学院'
    return raw


# 研究生应用管理平台数据的处理，和本科生保持一致
def regulate_dept_gs(raw: str) -> str:
    raw = raw[5:]
    if raw == "上海交大-密西根大学联合学院":
        return "密西根学院"
    if raw.startswith("电子信息与电气工程学院"):
        return "电子信息与电气工程学院"
    return raw


def regulate_gs_course_name(raw: str) -> str:
    raw = raw.removesuffix("(研）")
    raw = raw.removesuffix("（研）")
    raw = raw.removesuffix("(研)")
    return raw


def get_former_codes(base_dir: str) -> dict[str, str]:
    former_codes: dict[str, str] = dict()
    with open(f'{base_dir}/former_code.csv', mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            former_codes[row['old_code']] = row['new_code']
    return former_codes


def regulate_categories(line: dict[str, str]) -> set[str]:
    origin_categories: list[str] = line['通识课归属模块'].split(',')
    categories: set[str] = set()
    code = line['课程号']
    department = line['开课院系']

    fresh_reg = re.compile(r"01\d{2}")
    for origin_category in origin_categories:
        category = origin_category.removesuffix("（致远）")
        category = category.removesuffix("（2022）")
        category = category.removesuffix("（2022，致远）")
        if category == "数学或逻辑学" or category == "自然科学与工程技术":
            continue
        if category != "":
            categories.add(category)

    if len(categories) == 0 and department == '研究生院':
        categories.add('研究生')
    if len(categories) == 0 and line['年级'] == "0":
        if code.startswith('SP') or fresh_reg.search(code):
            categories.add('新生研讨')
        else:
            categories.add('通选')
    if len(categories) == 0 and any(code.startswith(x) for x in ['PE001C', 'PE002C', 'PE003C', 'PE004C']):
        categories.add('体育')

    return categories


class UploadData:
    departments: set[str] = set()
    categories: set[str] = set()
    teachers: set[tuple] = set()
    _raw_courses: set[tuple] = set()
    courses: set[tuple] = set()
    _course_department: dict[tuple[str, str], str] = dict()

    def deal_with_honor_courses(self):
        for course in self._raw_courses:
            other_dept = self._course_department.get((course[0], course[5]), '')  # code, tid
            if course[3] == '致远学院' and other_dept != '' and other_dept != '致远学院':
                continue
            self.courses.add(course)

    def deal_with_teacher_group(self, line: dict[str, str]) -> list[str]:
        teacher_group = line['合上教师']
        if teacher_group == 'QT2002231068/THIERRY; Fine; VAN CHUNG/无[外国语学院]':
            teacher_group = 'QT2002231068/THIERRY, Fine, VAN CHUNG/无[外国语学院]'
        teacher_group = teacher_group.split(';')
        ids: list[str] = []
        for teacher in teacher_group:
            try:
                tid, name, title = teacher.split('/')
            except ValueError:
                continue
            department = regulate_department(title[title.find('[') + 1:-1])
            title = title[0:title.find('[')]
            name_pinyin = ''.join(lazy_pinyin(name))
            abbr_pinyin = ''.join([i[0] for i in pinyin(name, style=Style.FIRST_LETTER)])
            self.teachers.add((tid, name, title, department, name_pinyin, abbr_pinyin))
            ids.append(tid)
            self.departments.add(department)
        return ids

    def clean_data_for_gs(self, jwc_csv: csv.DictReader, gs_csv: csv.DictReader):
        code_dept = dict()
        for line in gs_csv:
            code = line["KCDM"]
            dept = regulate_dept_gs(line["KCKKDWMC"])
            if code_dept.get(code, None) is None:
                code_dept[code] = dept
            else:
                if code_dept.get(code) != dept:
                    print(line)

        for line in jwc_csv:
            department = line['开课院系']

            if department != '研究生院':  # 只处理研究生课程
                continue
            name = regulate_gs_course_name(line['课程名称'])
            code = line['课程号']
            try:
                department = code_dept[code]
            except KeyError:
                continue
            teacher_ids = self.deal_with_teacher_group(line)
            self.departments.add(department)
            categories = ["研究生"]
            for category in categories:
                self.categories.add(category)

            main_teacher = line['任课教师'].split('|')[0] if line['任课教师'] else teacher_ids[0]

            # code	name	credit	department	category    main_teacher	teacher_group
            self.courses.add(
                (code, name, line['学分'], department, ";".join(categories),
                 main_teacher, ";".join(teacher_ids)))

    def clean_data_for_jwc(self, csv_reader, base_dir: str):

        for line in csv_reader:
            department = line['开课院系']
            if department == '研究生院':  # 跳过所有的研究生课程（主要原因是没有main_teacher字段）
                continue
            teacher_ids = self.deal_with_teacher_group(line)
            self.departments.add(department)
            categories = regulate_categories(line)
            for category in categories:
                self.categories.add(category)

            name = line['课程名称']
            code = line['课程号']
            try:
                main_teacher = line['任课教师'].split('|')[0] if line['任课教师'] else teacher_ids[0]
            except IndexError:
                print(line)
                continue
            if department != '致远学院':
                # 有些课程，显示致远学院和非致远学院同时开课，实际上是同一门课，这里取非致远
                self._course_department[(code, main_teacher)] = department
            # code	name	credit	department	category    main_teacher	teacher_group
            self._raw_courses.add(
                (code, name, line['学分'], department, ";".join(categories),
                 main_teacher, ";".join(teacher_ids)))

        self.deal_with_honor_courses()

    def get_courses(self):
        data = tablib.Dataset()
        data.headers = ['code', 'name', 'credit', 'department', 'categories', 'main_teacher', 'teacher_group']
        for course in self.courses:
            data.append(course)
        return data

    def get_teachers(self):
        data = tablib.Dataset()
        data.headers = ['tid', 'name', 'title', 'department', 'pinyin', 'abbr_pinyin']
        for teacher in self.teachers:
            data.append(teacher)
        return data
