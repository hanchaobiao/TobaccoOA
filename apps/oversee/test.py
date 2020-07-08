# -*- coding: utf-8 -*-
# @Time    : 2019/8/15 17:38
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : test.py
# @Software: 接口测试
import os
import datetime
import requests

from apps.admin.test import headers, login

web_url = "http://127.0.0.1:5001"

# web_url = "http://47.99.51.135:8010"


login()


def task_release():
    """
    任务发布
    :return:
    """

    data = {"is_dp": 0}
    response = requests.get(f"{web_url}/task/release", headers=headers, params=data)
    print(response.text)

    # data = {"id": 21}
    # response = requests.get(f"{web_url}/task/release", headers=headers, params=data)
    # print(response.text)

    # data = {
    #     "type": "重大事务",
    #     "name": "提升销量",
    #     "task_no": "A1000",
    #     "file_ids": [1,3],
    #     "introduce": "测试一下",
    #     "oversee_id": 2,
    #     "start_time": "2020-05-10 00:00:00",
    #     "end_time": "2020-05-20 00:00:00",
    #     "oversee_details": [
    #         {
    #             "name": "开动员会",
    #             "introduce": "动员全体员工",
    #             "agent_id": 3,
    #             "department_id":  2,
    #             "start_time": "2020-05-08 00:00:00",
    #             "end_time": "2020-05-10 00:00:00",
    #             "coordinator_ids": [1]
    #         }
    #     ]
    # }
    # response = requests.post(f"{web_url}/task/release", headers=headers, json=data)
    # print(response.text)

    # update_data = {
    #     "id": 10,
    #     "type": "专项事务",
    #     "name": "学习党建",
    #     "file_names": ["中央二号文件"],
    #     "introduce": "测试一下",
    #     "oversee_id": 2,
    #     "start_time": "2020-05-08 00:00:00",
    #     "end_time": "2020-05-10 00:00:00",
    #     "oversee_details": [
    #         {
    #             "id": 8,
    #             "name": "开动员会",
    #             "introduce": "动员全体员工",
    #             "agent_id": 3,
    #             "department_id":  2,
    #             "start_time": "2020-05-08 00:00:00",
    #             "end_time": "2020-05-14 00:00:00",
    #             "coordinator_ids": [1]
    #         }
    #     ]
    # }
    # data = {"id": 42, "name": "襄城分局", "leader_id": 2}
    # response = requests.put(f"{web_url}/task/release", headers=headers, json=update_data)
    # print(response.text)
    #
    # data = {"id": 1}
    # response = requests.delete(f"{web_url}/task/release", headers=headers, json=data)
    # print(response.text)


def submit_task():
    data = {
        "id": 8,
        "delete_file_ids": [1, 2],
        "submit_remark": "按时完成任务"
    }
    files = {
        "file": open('/Users/hanchaobiao/Downloads/杨芳求职经验分享海报.png', 'rb')
    }
    response = requests.put(f"{web_url}/task/submit", headers=headers, data=data, files=files)
    print(response.text)


def audit_task():
    data = {
        "id": 8,
        "status": "任务完成",
        "audit_remark": "任务完成较好"
    }
    response = requests.put(f"{web_url}/task/audit", headers=headers, json=data)
    print(response.text)


def upload_file():
    """
    上传文件
    :return:
    """
    data = {
        "file": open('/Users/hanchaobiao/code/student/python/flask/TobaccoOA/media/襄阳烟草市局员工名单.xls', 'rb')
    }
    response = requests.post(f"{web_url}/fileManage", headers=headers, files=data)
    print(response.text)


def delete_admin():
    """
    测试导入员工数据
    :return:
    """
    response = requests.delete(f"{web_url}/admin/manage", headers=headers, json={"ids": [3, 11]})
    print(response.text)


def oversee_message():
    """
    督办消息
    :return:
    """
    data = {"type": 'send'}
    response = requests.get(f"{web_url}/task/overseeMessage", headers=headers, params=data)
    print(response.text)

    # data = {"task_detail_id": 7, "content": "请尽快完成任务，快要逾期了"}
    # response = requests.post(f"{web_url}/task/overseeMessage", headers=headers, json=data)
    # print(response.text)

    # data = {"id": 1}
    # response = requests.put(f"{web_url}/task/overseeMessage", headers=headers, json=data)
    # print(response.text)


if __name__ == "__main__":
    # department_test()
    # upload_file()
    task_release()
    # audit_task()
    # submit_task()
    # oversee_message()
