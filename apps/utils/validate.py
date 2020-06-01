# -*- coding: utf-8 -*-
# @Time    : 2019/12/20 11:14
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : validate.py
# @Software: PyCharm


ALLOW_FILE_FORMAT = ["jpg", "jpeg", "png", "gif", "doc", "docx", "xls", "xlsx", "pdf"]


def allowed_file(filename):
    if filename.split(".")[-1] not in ALLOW_FILE_FORMAT:
        return False
    return True
