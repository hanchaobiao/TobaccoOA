# -*- coding: utf-8 -*-
# @Time    : 2019/12/20 11:14
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : validate.py
# @Software: PyCharm


def validate_phone(value, name):
    """
    手机号验证
    :param value:
    :param name:
    :return:
    """
    import re
    t = re.compile(r'^1(3\d|4[4-9]|5[0-35-9]|6[67]|7[013-8]|8[0-9]|9[0-9])\d{8}$')
    s = re.search(t, value)
    if s:
        return value
    else:
        raise ValueError(name + "：格式错误")


def validate_length(value, name):
    if 6 <= len(value) <= 16:
        return value
    else:
        raise ValueError(name + "：长度必须为6-16字符")
