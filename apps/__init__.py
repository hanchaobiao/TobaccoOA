# -*- coding: utf-8 -*-
# @Time    : 2019/4/28 19:54
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : __init__.py.py
# @Software: PyCharm
import os
import sys
from flask_cors import *
from flask import Flask, send_from_directory
from flask_restful import Api

from common.exception import InvalidUsage
from common.logger import logger
from common.response import json_response


app = Flask(__name__, static_folder='../media', static_url_path='/local_media')

api = Api(app, catch_all_404s=True)

app.debug = False
app.url_map.strict_slashes = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_PATH = os.path.join(BASE_DIR, 'media')

sys.path.insert(0, BASE_DIR)


CORS(app, supports_credentials=True)

from apps.admin import urls
from apps.admin_operation import urls
from apps.oversee import urls
from apps.wish import urls
from apps.report import urls


def handle_500(e):
    import traceback
    traceback.print_exc()
    logger.error(traceback.format_exc())
    if hasattr(e, 'code') and e.code == 400:  # 表单验证未通过
        return json_response(code=1, status_code=e.code, message=list(e.data['message'].values())[0])
    elif hasattr(e, 'description'):
        return json_response(code=1, message=e.description)
    elif hasattr(e, 'args'):
        return json_response(code=1, message=e.args[0])
    else:
        return json_response(code=1, message="未知异常")


# 自定义全局异常处理
api.handle_error = handle_500


# 访问上传的文件
# # 浏览器访问：http://127.0.0.1:5000/images/django.jpg/  就可以查看文件了
# @app.route('/media/<filename>/', methods=['GET','POST'])
# def get_image(filename):
#     return send_from_directory(MEDIA_PATH, filename)
