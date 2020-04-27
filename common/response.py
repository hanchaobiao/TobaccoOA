# -*- coding: utf-8 -*-
# @Time    : 2019/4/29 14:31
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : response.py
# @Software: 封装response
import json
from datetime import datetime, date
from decimal import Decimal

from flask import make_response

from resources.base import BaseDb


def json_serial(obj):
    """
    json dumps 特殊类型处理
    :param obj:
    :return:
    """
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, date):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type {}s not serializable".format(type(obj)))


def json_response(code=0, message="请求成功", data={}, errors={}, status_code=200):
    """
    将视图函数返回的数据转换成response对象
    :param code: 消息状态码
    :param message: 状态信息
    :param data: 数据
    :param errors: 表单错误信息
    :param status_code: 表单错误信息
    :return:
    """
    if code == 1 and message == '请求成功':
        message = '请求失败'
    if errors:
        code = 1
        for item in errors.items():
            message = item[0]
    result = {"code": code, "message": message, "data": data, "errors": errors}
    response = make_response(json.dumps(result, ensure_ascii=False, default=json_serial), status_code)
    response.content_type = 'application/json; charset=utf-8'
    return response
