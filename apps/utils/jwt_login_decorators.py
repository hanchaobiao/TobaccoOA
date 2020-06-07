# -*- coding: utf-8 -*-
# @Time    : 2019/3/22 15:52
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : jwt_login_decorators.py
# @Software: 装饰器
import os
import functools

from flask import request
import jwt

from resources.redis_pool import RedisPool
from module.AdminDb import AdminModel
from settings import JWT_EXPIRE, SECRET_KEY
from common.response import json_response


def admin_login_req(method):
    """
    是否登陆判断
    :param method:
    :return:
    """
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        if request.user_agent.browser is None:
            return json_response(code=403, message="非法访问", status_code=403)
        token = request.headers.get("token", request.values.to_dict().get('token'))
        if token:
            # 解密
            try:
                send_data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'],
                                       leeway=JWT_EXPIRE, options={"verify_exp": True})
                admin = RedisPool().get_admin(send_data['id'])
                # admin = {'id': 2, 'username': 'hancb', 'real_name': '韩朝彪', 'phone': '17600093237', 'sex': '男', 'position': '经理', 'department_id': 1, 'is_disable': 0, 'is_delete': 0, 'role_id': 1, "role_level": 9}
                if admin is None:
                    return json_response(code=402, message="请重新登陆")
                if admin['is_disable']:
                    return json_response(code=1, message="账户被禁用")
                request.user = admin  # 赋值
                return method(*args, **kwargs)
            except jwt.ExpiredSignatureError as e:  # 签名过期
                print(e)
                return json_response(code=402, message="签名过期，请重新登陆")
            except jwt.InvalidSignatureError as e:
                print(e)
                return json_response(code=402, message="签名错误，请重新登陆")
        else:
            return json_response(code=402, message="请登录")
    return wrapper
