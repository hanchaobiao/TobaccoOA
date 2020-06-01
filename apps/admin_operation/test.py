# -*- coding: utf-8 -*-
# @Time    : 2019/8/15 17:38
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : test.py
# @Software: 接口测试
import os
import requests

from apps.admin.test import headers


# web_url = "http://127.0.0.1:5001"

web_url = "http://47.99.51.135:8010"


def department_test():
    """
    部门管理测试
    :return:
    """
    response = requests.get(f"{web_url}/department", headers=headers, params={"pid": 1})
    print(response.text)

    data = {"name": "", "pid": 1, "leader_id": 1}
    response = requests.post(f"{web_url}/department", headers=headers, json=data)
    print(response.text)

    # data = {"id": 42, "name": "襄城分局", "leader_id": 2}
    # response = requests.put(f"{web_url}/department", headers=headers, json=data)
    # print(response.text)

    # data = {"id": 42, "name": "襄城分局", "leader_id": 2}
    # response = requests.delete(f"{web_url}/department", headers=headers, json=data)
    # print(response.text)


def get_file_list():
    response = requests.get(f"{web_url}/fileManage", headers=headers, params={"file_name": "襄阳烟"})
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


if __name__ == "__main__":
    department_test()
    # upload_file()
    # get_file_list()
