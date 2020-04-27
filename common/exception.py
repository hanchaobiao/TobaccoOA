# -*- coding: utf-8 -*-
# @Time    : 2019/4/29 16:05
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : exception.py
# @Software: 自定义异常


class InvalidUsage(Exception):
    """
    自定义异常
    """
    def __init__(self, code, status_code, message):
        Exception.__init__(self)
        self.status_code = status_code
        self.code = code
        self.message = message
