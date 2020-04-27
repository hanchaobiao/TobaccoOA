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
from apps.admin_operation.forms import AddDepartmentForm, UpdateDepartmentForm
from module.AdminDb import AdminModel
from module.DepartmentDb import DepartmentModel
from module.FileManageDb import FileManageModel
from common.response import json_response
from apps.utils.jwt_login_decorators import admin_login_req
from resources.redis_pool import RedisPool


from flask_restful import Resource

from common.operate_log import AdminOperateLog


class BaseResource(Resource, AdminOperateLog):

    def __init__(self):
        Resource.__init__(self)
        AdminOperateLog.__init__(self)


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


class DepartmentView(BaseResource):
    """
    部门管理
    """

    __table__ = 'dict_department'  # 操作表
    __table_desc__ = '部门'

    @staticmethod
    @admin_login_req
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("pid", type=int, help='部门id', required=False, default=None)
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
            self.insert_log(self.__table__, department['id'], desc='添加部门：{}'.format(form.data['name']),
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
                self.update_log(self.__table__, department['id'], desc="修改部门：{}".format(department['name']),
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
            self.delete_log(self.__table__, department['id'], '删除部门：{}'.format(department['name']), department)
            return json_response(data=department)
        else:
            return json_response(code=1, message='部门不存在')


class FileManageView(BaseResource):
    """
    文件管理
    """

    __table__ = 'sys_file_manage'

    @staticmethod
    def allowed_file(filename):
        if filename.split(".")[-1] not in ["jpg", "jpeg", "png", "gif", "doc", "docx", "xls", "xlsx", "pdf"]:
            return False
        return True

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
        for f in request.files.getlist('file'):
            file_info = dict()
            # 检查文件类型
            now_time = datetime.datetime.now()
            file_info['format'] = f.filename.split(".")[-1]
            file_info['file_name'] = f.filename.replace(".{}".format(file_info['format']), '')
            file_info['size'] = len(f.read())
            if f and self.allowed_file(f.filename):
                new_filename = str(now_time).replace(" ", '-') + '_' + f.filename
                base_bath = os.path.join(MEDIA_PATH, file_info['format'])
                if os.path.exists(base_bath) is False:
                    os.mkdir(base_bath)
                file_path = os.path.join(base_bath, new_filename)
                f.save(file_path)
                file_info['admin_id'] = request.user['id']
                file_info['add_time'] = now_time
                file_info['file_path'] = file_path.replace(MEDIA_PATH, '')
                model.insert_file_info(file_info)
                self.insert_log(self.__table__, file_info['id'], "上传文件：{}".format(f.filename), file_info)
        return json_response(code=1, message="上传成功")

    @admin_login_req
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='文件id', required=True)
        parser.add_argument("file_name", type=str, help='文件名', required=True)
        args = parser.parse_args()
        model = FileManageModel()
        file_info = model.get_file_by_id(args['id'])
        if file_info:
            num = model.update_execute(self.__table__, **args)
            if num:
                message = '修改文件名称{}->{}'.format(file_info['file_name'], args['file_name'])
                self.update_log(self.__table__, file_info['id'], message, file_info, args)
                return json_response(data=args)
            else:
                return json_response(code=1, message="文件名未改变")
        else:
            return json_response(code=1, message='文件不存在')


class DownloadFileView(BaseResource):
    """
    下载文件
    """


    def post(self):
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
