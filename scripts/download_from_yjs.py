import csv
import json

import requests

url = "http://yjs.sjtu.edu.cn/gsapp/sys/kccxapp/modules/kccx/kcxxcx.do"

headers = {
    'Connection': 'keep-alive',
    'Cookie': '',
    'DNT': '1',
    'Origin': 'http://yjs.sjtu.edu.cn',
    'Referer': 'http://yjs.sjtu.edu.cn/gsapp/sys/kccxapp/*default/index.do?THEME=purple&amp;EMAP_LANG=zh',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.33',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'x-requested-with': 'XMLHttpRequest'
}

courses = []
page = 1
while page <= 5:
    payload = f"KKZTDM=1&querySetting=%5B%7B%22name%22%3A%22KKZTDM%22%2C%22caption%22%3A%22%E5%BC%80%E8%AF%BE%E7%8A%B6%E6%80%81%22%2C%22linkOpt%22%3A%22AND%22%2C%22builderList%22%3A%22cbl_m_List%22%2C%22builder%22%3A%22m_value_equal%22%2C%22value%22%3A%221%22%7D%5D&KCBQ=&pageSize=999&pageNumber={page}"
    response = requests.request("POST", url, headers=headers, data=payload)
    resp = response.json()
    print(len(resp["datas"]["kcxxcx"]["rows"]))
    courses = courses + resp["datas"]["kcxxcx"]["rows"]
    page = page + 1

with open("../data/yjs-data-1.csv", mode='w', encoding='utf-8-sig', newline="") as f:
    # 课程性质 课程代码 上课方式 课程分类 课程名称
    writer = csv.DictWriter(f, fieldnames=["KCXZDM_DISPLAY", "KCDM", "SKFSDM_DISPLAY", "KCFLDM_DISPLAY", "KCMC",
                                           # 成绩记录方式 课程负责人姓名 开课单位
                                           "CJJLFSDM_DISPLAY", "KCFZRXM", "KKDW_DISPLAY",
                                           # 上课语言 课程层次 学分 考试类型
                                           "SKYYDM_DISPLAY", "KCCCDM_DISPLAY", "XF", "KSLXDM_DISPLAY"],
                            extrasaction='ignore')
    writer.writeheader()
    writer.writerows(courses)
