# -*- coding: utf-8 -*-
# @Time    : 2019/6/19 20:16
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : permissions_auth.py
# @Software: PyCharm
# @Software: 装饰器
import functools
from flask import request
from common.response import json_response


def allow_role_req(role_ids=[1]):
    """
    允许哪些权限请求
    :param role_ids:
    :return:
    """
    def permissions_auth_req(method):
        """
        验证手机号是否已经绑定
        :param method:
        :return:
        """
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            admin = request.user
            if admin['role_id'] not in role_ids:
                return json_response(code=1, message="权限不足")
            return method(*args, **kwargs)
        return wrapper
    return permissions_auth_req
