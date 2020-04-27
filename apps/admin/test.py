# -*- coding: utf-8 -*-
# @Time    : 2019/8/15 17:38
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : test.py
# @Software: 接口测试
import os

import requests

# web_url = "http://127.0.0.1:5001/report"

web_url = "http://127.0.0.1:5001"

headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
}


def login():
    """
    测试登陆
    :return:
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
    }
    response = requests.post(f"{web_url}/login", params={"username": "hancb", "password": "123456"}, headers=headers)
    print(response.text)
    print(response.json())
    return response.json()['data']['token']


# token = test_login()

token = ''

headers = {
    "token": token
}


def update_password():
    """
    测试修改密码
    :return:
    """
    response = requests.put(f"{web_url}/admin/updatePassword", headers=headers, json={"password": "123456", "confirm_password": "123456", "old_password": "123qwe"})
    print(response.json())


def get_login_log():
    """
    测试导入员工数据
    :return:
    """
    params = {"name": "韩", "start_time": "2020-04-20", "end_time": "2020-04-21", "sort": "DESC"}
    response = requests.get(f"{web_url}/admin/loginLog", headers=headers, params=params)
    print(response.json())


def get_operate_log():
    """
    测试导入员工数据
    :return:
    """
    params = {"name": "韩", "start_time": "2020-04-20", "end_time": "2020-04-22", "sort": "DESC"}
    response = requests.get(f"{web_url}/admin/operateLog", headers=headers, params=params)
    print(response.json())
    params = {"id": 10}
    response = requests.get(f"{web_url}/admin/operateLog", headers=headers, params=params)
    print(response.json())


def get_admin():
    """
    测试导入员工数据
    :return:
    """
    response = requests.get(f"{web_url}/admin/manage", headers=headers, params={"nickname": "测试"})
    print(response.json())


def post_admin():
    """
    测试导入员工数据
    :return:
    """
    data = {"username": "liuyuxiao", "password": "123qwe", "real_name": "刘雨潇", "phone": "17600093237", "sex": "男",
            "position": "经理", "department_id": 3, "is_disable": False}
    response = requests.post(f"{web_url}/admin/manage", headers=headers, json=data)
    print(response.text)


def put_admin():
    """
    测试导入员工数据
    :return:
    """
    data = {"id": 3, "username": "liuyuxiao", "password": "123qwe", "real_name": "刘雨潇", "phone": "17600093237", "sex": "男",
            "position": "主任", "department_id": 3, "is_disable": False}
    response = requests.put(f"{web_url}/admin/manage", headers=headers, json=data)
    print(response.text)


def delete_admin():
    """
    测试导入员工数据
    :return:
    """
    response = requests.delete(f"{web_url}/admin/manage", headers=headers, json={"ids": [3, 11]})
    print(response.text)


if __name__ == "__main__":
    # pass
    # test_login()
    # get_login_log()
    # get_operate_log()
    # test_update_password()
    # test_get_admin()
    # post_admin()
    put_admin()
    # test_delete_admin()