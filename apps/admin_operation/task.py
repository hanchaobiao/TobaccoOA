# -*- coding: utf-8 -*-
# @Time    : 2019/5/5 18:08
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : task.py
# @Software: 异步任务
import os
import datetime

from flask import request

from apps import MEDIA_PATH
from apps.utils.validate import allowed_file, ALLOW_FILE_FORMAT


def upload_file(dir_name, **kwargs):
    file_list = []
    for f in request.files.getlist('file'):
        if allowed_file(f.filename) is False:
            return {"code": 1, "message": "文件格式不符合，只允许上传如下格式文件：{}".format(str(ALLOW_FILE_FORMAT))}
    for f in request.files.getlist('file'):
        file_info = dict()
        # 检查文件类型
        now_time = datetime.datetime.now()
        file_info.update(kwargs)
        file_info['file_name'] = f.filename
        file_info['format'] = f.filename.split(".")[-1]
        file_info['size'] = len(f.read())
        new_filename = str(now_time).replace(" ", '-') + '_' + f.filename
        base_bath = os.path.join(MEDIA_PATH, dir_name, now_time.strftime('%Y%m'))
        if os.path.exists(base_bath) is False:
            print(base_bath)
            os.makedirs(base_bath)
        file_path = os.path.join(base_bath, new_filename)
        f.save(file_path)
        file_info['add_time'] = now_time
        file_info['admin_id'] = request.user['id']
        file_info['file_path'] = file_path.replace(MEDIA_PATH, '')
        file_list.append(file_info)
    return {"code": 0, "data": file_list}
