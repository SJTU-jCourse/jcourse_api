import csv
import json

with open('../data/allcourse_yjs.json', mode='r', encoding='utf-8') as f:
    obj = json.load(f)
    courses = obj['datas']

with open("../data/yjs-data-1.csv", mode='w', encoding='utf-8-sig', newline="") as f:
    # 课程性质 课程代码 上课方式 课程分类 课程名称
    writer = csv.DictWriter(f, fieldnames=["KCXZDM", "KCDM", "SKFSDM", "KCFLDM", "KCMC",
                                           # 成绩记录方式 课程负责人姓名 开课单位
                                           "CJJLFSDM", "RKJS", "KCKKDWMC",
                                           # 上课语言 课程层次 学分 考试类型
                                           "SKYYMC", "KCCCMC", "KCXF", "KSLXDM"],
                            extrasaction='ignore')
    writer.writeheader()
    writer.writerows(courses)
