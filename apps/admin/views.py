# -*- coding: utf-8 -*-
# @Time    : 2019/4/28 19:55
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : views.py
# @Software: PyCharm
import datetime
import hashlib

from flask import request
from flask_restful import Resource, reqparse
from module.AdminDb import AdminModel
from module.DepartmentDb import DepartmentModel
from common.response import json_response
from apps.utils.jwt_login_decorators import admin_login_req
from resources.redis_pool import RedisPool
from apps.admin_operation.views import BaseResource


from ..admin.forms import *


class LoginView(Resource):

    @staticmethod
    def post():
        """
        登陆
        :return:
        """
        parser = reqparse.RequestParser()
        parser.add_argument("username", type=str, help="用户名长度字符",  required=True)
        parser.add_argument("password", type=str, help="密码不符合规范", required=True)
        args = parser.parse_args()
        model = AdminModel()
        result = model.login(args['username'], args['password'])
        if result['code'] == 0:
            RedisPool().set_online_status(result['data']['admin'])
        return json_response(**result)


class LogoutView(Resource):

    @staticmethod
    @admin_login_req
    def post():
        """
        登陆
        :return:
        """
        RedisPool().set_offline_status(request.user['id'])
        return json_response(message='退出成功')


class AdminLoginLogView(Resource):

    @staticmethod
    @admin_login_req
    def get():
        """
        登陆
        :return:
        """
        parser = reqparse.RequestParser()
        print(request.values.to_dict())
        parser.add_argument("name", type=str, help="用户名", required=False)
        parser.add_argument("start_time", type=str, help="开始时间", required=True, default=datetime.datetime.now().date())
        parser.add_argument("end_time", type=str, help="结束时间", required=True, default=datetime.datetime.now())
        parser.add_argument("sort", type=str, choices=['ASC', 'DESC'], help="排序类型", required=False, default='DESC')
        parser.add_argument("page", type=int, help="页码", required=False, default=1)
        parser.add_argument("page_size", type=int, help="页数", required=False, default=20)
        args = parser.parse_args()
        admin = AdminModel()
        result = admin.get_login_log_list(admin, args['name'], args['start_time'], args['end_time'], args['sort'],
                                          args['page'], args['page_size'])
        return json_response(data=result)


class AdminOperateLogView(Resource):

    @staticmethod
    @admin_login_req
    def get():
        """
        操作日志
        :return:
        """
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=str, help="id", required=False, default=None)
        parser.add_argument("admin_id", type=str, help="操作人", required=False)
        parser.add_argument("operate_type", type=str, help="操作类型", required=False)
        parser.add_argument("start_time", type=str, help="开始时间", required=False, default=datetime.datetime.now().date())
        parser.add_argument("end_time", type=str, help="结束时间", required=False, default=datetime.datetime.now())
        parser.add_argument("sort", type=str, choices=['ASC', 'DESC'], help="排序类型", required=False, default='DESC')
        parser.add_argument("page", type=int, help="页码", required=False, default=1)
        parser.add_argument("page_size", type=int, help="页数", required=False, default=20)
        args = parser.parse_args()
        admin = AdminModel()
        if args['id']:
            result = admin.get_operate_log_detail(int(args['id']))
        else:
            result = admin.get_operate_log_list(admin, args['admin_id'], args['operate_type'], args['start_time'],
                                                args['end_time'], args['sort'], args['page'], args['page_size'])
        return json_response(data=result)


class UpdatePasswordView(Resource):
    """
    修改个人密码
    """

    @staticmethod
    @admin_login_req
    def put():
        """
        :return:
        """
        form = UpdatePasswordForm().from_json(request.json)
        if form.validate():
            model = AdminModel()
            if form.data['password'] != form.data['confirm_password']:
                return json_response(code=1, message="两次密码输入不一致")
            if form.data['password'] == form.data['old_password']:
                return json_response(code=1, message='修改后的密码不能与之前一致')
            admin = request.user
            admin = model.get_admin_by_username(admin['username'])
            form.old_password.data = model.get_md5_password(form.data['old_password'])
            if form.old_password.data != admin['password']:
                return json_response(code=1, message='密码错误')
            form.password.data = model.get_md5_password(form.data['password'])
            model.update_password(admin, form.data['password'])
            RedisPool().set_offline_status(admin['id'])  # 设置离线状态，从新登陆
            form.id = admin['id']
            return json_response(message='修改成功', form=form, old_value=admin)
        else:
            return json_response(errors=form.errors)


class AdminManageView(BaseResource):
    """
    员工信息管理
    """

    __table__ = 'sys_admin'

    @staticmethod
    @admin_login_req
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=str, help='部门id', required=False)
        parser.add_argument("real_name", type=str, help='用户名', required=False)
        parser.add_argument("phone", type=str, help='手机号', required=False)
        parser.add_argument("start_date", type=str, help='开始时间', required=False)
        parser.add_argument("end_date", type=str, help='结束时间', required=False)
        parser.add_argument("page", type=int, help='页码', required=False, default=1)
        parser.add_argument("page_size", type=int, help='页数', required=False, default=10)
        args = parser.parse_args()
        am = AdminModel()
        admin = request.user
        result = am.get_admin_list(admin, args['real_name'], args['department_id'], args['phone'],
                                   args['start_date'], args['end_date'], args['page'], args['page_size'])
        return json_response(data=result)

    @admin_login_req
    def post(self):
        form = AddAdminForm().from_json(request.json)
        if form.validate():
            model = AdminModel()
            result = model.add_admin(form.data)
            if result['code'] == 0:
                admin = result['data']
                self.insert_log(self.__table__, admin['id'], "新增用户：{}".format(admin['real_name']), admin)
            return json_response(**result)
        else:
            return json_response(code="FAIL", message="表单验证异常", errors=form.errors)

    @admin_login_req
    def put(self):
        form = UpdateAdminForm().from_json(request.json)
        if form.validate():
            model = AdminModel()
            user = model.get_admin_by_id(form.data['id'])
            if user:
                if form.data['password']:
                    form.password.data = model.get_md5_password(form.password.data)
                else:
                    del form.data['password']
                count = model.update_execute(model.table_name, **form.data)
                if count:
                    RedisPool().set_offline_status(form.data['id'])  # 设置离线
                    self.update_log(self.__table__, user['id'], "修改用户：{}".format(user['real_name']),
                                    user, form.data)
                return json_response(data=form.data)
            else:
                return json_response(code=1, message="用户不存在")
        else:
            return json_response(code="FAIL", message="表单验证异常", errors=form.errors)

    @admin_login_req
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='部门id', required=True)
        args = parser.parse_args()
        num = DepartmentModel().is_department_leader(args['id'])
        if num:
            return json_response(code=1, message="部门负责人，不能删除")
        model = AdminModel()
        user = model.get_admin_by_id(args['id'])
        if user:
            RedisPool().set_offline_status(args['id'])  # 设置离线
            count = model.delete_admin(args['id'])
            if count:
                self.delete_log(self.__table__, user['id'], "删除用户：{}".format(user['real_name']), user)
            return json_response(data=user)
        else:
            return json_response(code=1, message="用户不存在")
