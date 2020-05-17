# -*- coding: utf-8 -*-
# @Time    : 2019/4/28 19:55
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : views.py
# @Software: PyCharm
import os
import datetime
import hashlib
from copy import deepcopy

from flask import request, make_response
from flask_restful import Resource, reqparse
from apps import MEDIA_PATH
from apps.wish.forms import AddWishForm
from module.OverseeTaskDb import OverseeTaskModel
from module.WishDb import WishModel
from common.response import json_response
from apps.utils.db_transaction import db_transaction
from apps.utils.jwt_login_decorators import admin_login_req
from resources.redis_pool import RedisPool


class AuditWishView(Resource):
    """
    心愿
    """

    __table__ = 'employee_wish'  # 操作表
    __table_desc__ = '心愿'

    @admin_login_req
    def post(self):
        form = AddWishForm().from_json(request.json)
        if form.validate():
            data = dict(form.data)
            data['add_time'] = datetime.datetime.now()
            data['status'] = 0
            data['employee_id'] = request.user['id']
            model = WishModel()
            task = model.execute_insert(self.__table__, data)
            # self.insert_log(self.__table__, task['id'], '发布督办任务：{}'.format(task['name']), task)
            return json_response(data=task, message="添加成功")
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=str, help='心愿id', required=False, default=None)
        args = parser.parse_args()
        model = WishModel()
        task = model.execute_delete(self.__table__, args['id'], ['status=0'])
        if task == 1:
            # self.insert_log(self.__table__, task['id'], '发布督办任务：{}'.format(task['name']), task)
            return json_response(data=task, message="删除成功")
        return json_response(data=task, message="当前状态无法删除")


class EmployeeWishView(Resource):
    """
    心愿
    """

    __table__ = 'employee_wish'  # 操作表
    __table_desc__ = '心愿'

    @admin_login_req
    def post(self):
        form = AddWishForm().from_json(request.json)
        if form.validate():
            data = dict(form.data)
            data['add_time'] = datetime.datetime.now()
            data['status'] = 0
            data['employee_id'] = request.user['id']
            model = WishModel()
            task = model.execute_insert(self.__table__, data)
            # self.insert_log(self.__table__, task['id'], '发布督办任务：{}'.format(task['name']), task)
            return json_response(data=task, message="添加成功")
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=str, help='心愿id', required=False, default=None)
        args = parser.parse_args()
        model = WishModel()
        task = model.execute_delete(self.__table__, args['id'], ['status=0'])
        if task == 1:
            # self.insert_log(self.__table__, task['id'], '发布督办任务：{}'.format(task['name']), task)
            return json_response(data=task, message="删除成功")
        return json_response(data=task, message="当前状态无法删除")
