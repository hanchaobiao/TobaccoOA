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

import pymysql
from flask import request, make_response
from flask_restful import Resource, reqparse
from apps import MEDIA_PATH
from apps.admin_operation.forms import AddDepartmentForm, UpdateDepartmentForm, AddMemoEventForm, UpdateMemoEventForm
from module.AdminDb import AdminModel
from module.AdminOperateDb import AdminOperateModel
from module.DepartmentDb import DepartmentModel
from module.FileManageDb import FileManageModel
from common.response import json_response
from apps.utils.jwt_login_decorators import admin_login_req
from apps.admin_operation.task import upload_file
from apps.oversee.task import send_sys_message


from flask_restful import Resource

from resources.base import BaseDb


class UseAdminView(Resource):

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("type", type=str, help='类型', required=False, default=None)
        args = parser.parse_args()
        if args['type'] == 'file':
            result = FileManageModel().get_distinct_admin_list()
        elif args['type'] == 'operate_log':
            result = AdminModel().get_operate_log_distinct_admin_list()
        elif args['type'] == 'login_log':
            result = AdminModel().get_login_log_distinct_admin_list()
        return json_response(code=0, data=result)


class AdminSelectView(Resource):

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=str, help='类型', required=False, default=None)
        parser.add_argument("role_id", type=str, help='类型', required=False, default=None)
        args = parser.parse_args()
        result = AdminModel().get_admin_by_department_role(args['department_id'], args['role_id'])
        return json_response(code=0, data=result)


class DepartmentView(Resource):
    """
    部门管理
    """

    __table__ = 'dict_department'  # 操作表
    __table_desc__ = '部门'

    @staticmethod
    @admin_login_req
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("pid", type=int, help='部门id', required=False, default=1)
        args = parser.parse_args()
        model = DepartmentModel()
        result = model.get_department_tree(args['pid'])
        return json_response(data=result)

    @admin_login_req
    def post(self):
        form = AddDepartmentForm().from_json(request.json)
        if form.validate():
            model = DepartmentModel()
            department = model.get_department_by_name(form.data['name'])
            if department:
                return json_response(code=1, message="部门名称已被使用")
            department = model.add_department(form.data)
            model.insert_log(self.__table__, department['id'], desc='添加部门：{}'.format(form.data['name']),
                             insert_data=department)
            return json_response(data=department)
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    def put(self):
        form = UpdateDepartmentForm().from_json(request.json)
        if form.validate():
            model = DepartmentModel()
            department = model.get_department_by_name(form.data['name'])
            if department and department['id'] != form.data['id']:
                return json_response(code=1, message="部门名称已被使用")
            elif department is None:
                department = model.get_department_by_id(form.data['id'])
            if department:
                count = model.update_department(form.data)
                if count == 0:
                    return json_response(code=1, message='数据未修改')
                new_data = deepcopy(department)
                new_data.update(form.data)
                model.update_log(self.__table__, department['id'], desc="修改部门：{}".format(department['name']),
                                 origin_data=department, new_data=new_data)
                return json_response(data=new_data)
            else:
                return json_response(code=1, message='部门不存在')
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='部门id', required=True)
        args = parser.parse_args()
        num = AdminModel().is_exists_admin_by_department(args['id'])
        if num:
            return json_response(code=1, message="部门存在员工，不能删除")
        model = DepartmentModel()
        num = model.is_exists_sub_department(args['id'])
        if num:
            return json_response(code=1, message="存在下级部门，不能删除")
        department = model.get_department_by_id(args['id'])
        if department:
            model.delete_department(args['id'])
            model.delete_log(self.__table__, department['id'], '删除部门：{}'.format(department['name']), department)
            return json_response(data=department)
        else:
            return json_response(code=1, message='部门不存在')


class FileManageView(Resource):
    """
    文件管理
    """

    __table__ = 'sys_file_manage'

    @admin_login_req
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("file_name", type=str, help='文件名', required=False, default=None)
        parser.add_argument("format", type=str, help='文件格式', required=False, default=None)
        parser.add_argument("admin_id", type=str, help='上传人', required=False, default=None)
        parser.add_argument("start_date", type=str, help='开始时间', required=False)
        parser.add_argument("end_date", type=str, help='结束时间', required=False)
        parser.add_argument("page", type=int, help='页码', required=False, default=1)
        parser.add_argument("page_size", type=int, help='页数', required=False, default=10)
        args = parser.parse_args()
        model = FileManageModel()
        result = model.get_file_list(args['file_name'], args['format'], args['admin_id'],
                                     args['start_date'], args['end_date'], args['page'], args['page_size'])
        return json_response(data=result)

    @admin_login_req
    def post(self):
        if 'file' not in request.files:
            return json_response(code=1, message='请选择文件')
        model = FileManageModel()
        try:
            model.start_transaction()
            file_list = upload_file('system')
            ids = model.execute_insert_many(self.__table__, file_list)
            for index, file_info in enumerate(file_list):
                file_info['id'] = ids[index]
                model.execute_insert(self.__table__, **file_info)
                model.insert_log(self.__table__, file_info['id'], file_info)
            model.conn.commit()
            return json_response(code=0, message="上传成功", data=file_list)
        except pymysql.err.IntegrityError:
            message = "文件名:{}已存在".format(file_info['file_name'])
        except Exception as e:
            print(e)
            message = str(e)
            model.conn.rollback()
        return json_response(code=1, message=message)

    @admin_login_req
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='文件id', required=True)
        parser.add_argument("file_name", type=str, help='文件名', required=True)
        args = parser.parse_args()
        model = FileManageModel()
        file_info = model.get_file_by_id(args['id'])
        if file_info:
            num = model.execute_update(self.__table__, args)
            if num:
                message = '修改文件名称{}->{}'.format(file_info['file_name'], args['file_name'])
                model.update_log(self.__table__, file_info['id'], message, file_info, args)
                return json_response(data=args)
            else:
                return json_response(code=1, message="文件名未改变")
        else:
            return json_response(code=1, message='文件不存在')


class DownloadFileView(Resource):
    """
    下载文件
    """

    @staticmethod
    def post():
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='文件id', required=True)
        args = parser.parse_args()
        try:
            file_info = FileManageModel().get_file_by_id(args['id'])
            if file_info:
                path = os.path.join(MEDIA_PATH, file_info['path'])
                with open(path, mode='rb') as f:
                    content = f.read()
                response = make_response(content)
                response.headers['Content-Type'] = file_info['format']
                filename = file_info['file_name']+'.'+file_info['format']
                response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename.encode().decode('latin-1'))
                return response
            else:
                return json_response(code=1, message='文件不存在')
        except Exception as err:
            print('download_file error: {}'.format(str(err)))
            return json_response(code=1, message='下载异常')


class MemoEventView(Resource):
    """
    备忘录
    """

    __table__ = 'memo_event'

    @admin_login_req
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("month", type=str, help='月份', required=True)
        args = parser.parse_args()
        result = AdminOperateModel().get_my_memo(request.user['id'], args['month'])
        return result

    @admin_login_req
    def post(self):
        form = AddMemoEventForm().from_json(request.json)
        if form.validate():
            try:
                data = dict(form.data)
                data['add_time'] = datetime.datetime.now()
                data['admin_id'] = request.user['id']
                AdminModel().execute_insert(self.__table__, **data)
            except pymysql.err.IntegrityError:
                return json_response(code=1, message="该日期已有备忘内容")
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    def put(self):
        form = UpdateMemoEventForm().from_json(request.json)
        if form.validate():
            model = AdminModel()
            memo = model.get_data_by_id(self.__table__, form.data['id'])
            if memo is None:
                return json_response(code=1, message="无此备忘记录")
            if memo['admin_id'] != request.user['id']:
                return json_response(code=1, message="无权限操作此备忘录")
            model.execute_update(self.__table__, form.data, memo)
            return json_response(code=0, message="修改成功")
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='id', required=True)
        args = parser.parse_args()
        model = AdminModel()
        memo = model.execute_delete(self.__table__, [f'id={args["id"]}', 'admin_id={}'.format(request.user['id'])])
        if memo is None:
            return json_response(code=1, message="无此备忘记录")
        if memo['admin_id'] != request.user['id']:
            return json_response(code=1, message="无权限操作此备忘录")
        model.execute_update(self.__table__, args, memo)
        return json_response(code=0, message="修改成功")


class ScheduleView(Resource):
    """
    行程安排
    """

    __table__ = 'schedule_event'

    @admin_login_req
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("month", type=str, help='月份', required=True)
        args = parser.parse_args()
        result = AdminOperateModel().get_my_memo(request.user['id'], args['month'])
        return result

    @admin_login_req
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("arranged_id", type=str, help='行程内容', required=True)
        parser.add_argument("content", type=str, help='行程内容', required=True)
        parser.add_argument("schedule_time", type=str, help='行程时间', required=True)
        args = parser.parse_args()
        try:
            if 1 not in request.user['role_ids'] and args['arranged_id'] != request.user['id']:
                return json_response(code=1, message="无权给此人安排行程")
            args['add_time'] = datetime.datetime.now()
            args['operator_id'] = request.user['id']
            AdminOperateModel().execute_insert(self.__table__, **args)
        except pymysql.err.IntegrityError:
            return json_response(code=1, message="该日期已有备忘内容")

    @admin_login_req
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='id', required=True)
        parser.add_argument("content", type=str, help='备忘内容', required=True)
        parser.add_argument("schedule_time", type=str, help='行程时间', required=True)
        args = parser.parse_args()
        model = AdminOperateModel()
        schedule = model.get_data_by_id(self.__table__, args['id'])
        if schedule is None:
            return json_response(code=1, message="无此备忘记录")
        if schedule['operator_id'] != request.user['id'] or 1 not in request.user['role_ids']:
            return json_response(code=1, message="无权限操作此备忘录")
        if 1 not in request.user['role_ids']:
            return json_response(code=1, message="无权给此人安排行程")
        model.execute_update(self.__table__, args, schedule)
        return json_response(code=0, message="修改成功")

    @admin_login_req
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='id', required=True)
        args = parser.parse_args()
        model = AdminOperateModel()
        schedule = model.get_data_by_id(self.__table__, args['id'])
        if schedule is None:
            return json_response(code=1, message="无此日程记录")
        if schedule['admin_id'] != request.user['id']:
            return json_response(code=1, message="无权限操作此日程")
        model.execute_delete(self.__table__, [f'id={args["id"]}', 'admin_id={}'.format(request.user['id'])])
        return json_response(code=0, message="删除成功")


class AdjustScheduleView(Resource):
    """
    调整行程安排
    """

    __table__ = 'schedule_event'

    @admin_login_req
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='id', required=True)
        parser.add_argument("schedule_time", type=str, help='行程时间', required=True)
        args = parser.parse_args()
        model = AdminOperateModel()
        schedule = model.get_data_by_id(self.__table__, args['id'])
        if schedule is None:
            return json_response(code=1, message="无此备忘记录")
        if schedule['admin_id'] != request.user['id']:
            return json_response(code=1, message="无权限操作此备忘录")
        model.execute_update(self.__table__, args, schedule)
        return json_response(code=0, message="修改成功")

