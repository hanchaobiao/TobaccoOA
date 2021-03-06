# -*- coding: utf-8 -*-
# @Time    : 2019/4/28 19:55
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : views.py
# @Software: PyCharm
import os
import datetime
import mimetypes
from copy import deepcopy

import pymysql
from flask import request, make_response
from flask_restful import Resource, reqparse
from apps import MEDIA_PATH
from apps.admin_operation.forms import AddDepartmentForm, UpdateDepartmentForm, AddMemoEventForm, UpdateMemoEventForm,\
    AddScheduleEventForm, UpdateScheduleEventForm, UpdateTaxProgressForm, AddDepartmentNoticeForm, UpdateDepartmentNoticeForm
from module.AdminDb import AdminModel
from module.AdminOperateDb import AdminOperateModel
from module.DepartmentDb import DepartmentModel
from module.FileManageDb import FileManageModel
from common.response import json_response
from apps.utils.jwt_login_decorators import admin_login_req
from apps.utils.permissions_auth import allow_role_req
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
        parser.add_argument("type", type=str, help='角色类型', choices=['oversee', 'agent', 'coordinator'], required=True)
        args = parser.parse_args()

        if args['type'] == 'oversee':
            role_ids = [1, 2, 3]
        elif args['type'] == 'agent':
            role_ids = [1, 4, 6]
        else:
            role_ids = [5]
        result = AdminModel().get_admin_by_department_role(args['department_id'], role_ids)
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
    @allow_role_req([1])
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
    @allow_role_req([1])
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
    @allow_role_req([1])
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
    @allow_role_req([1])
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
    @allow_role_req([1])
    def post(self):
        if 'file' not in request.files:
            return json_response(code=1, message='请选择文件')
        model = FileManageModel()
        try:
            model.start_transaction()
            result = upload_file('system')
            if result['code'] == 1:
                return json_response(**result)
            for index, file_info in enumerate(result['data']):
                file_id = model.execute_insert(self.__table__, **file_info)
                file_info['id'] = file_id
                model.insert_log(self.__table__, file_info['id'], "上传文件：{}".format(file_info['file_name']),
                                 file_info)
            model.conn.commit()
            return json_response(code=0, message="上传成功", data=result['data'])
        except pymysql.err.IntegrityError:
            message = "文件名:{}已存在".format(file_info['file_name'])
        except Exception as e:
            import traceback
            traceback.print_exc()
            message = str(e)
            model.conn.rollback()
        return json_response(code=1, message=message)

    @admin_login_req
    @allow_role_req([1])
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

    @admin_login_req
    @allow_role_req([1])
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='文件id', required=True)
        args = parser.parse_args()
        model = FileManageModel()
        file_info = model.get_data_by_id(self.__table__, args['id'])
        if file_info:
            flag = model.is_used_file(args['id'])
            if flag is False:
                model.execute_delete(self.__table__, ['id=%s' % args['id']])
                model.delete_log(self.__table__, args['id'], "删除文件：{}".format(file_info['file_name']), file_info)
                try:
                    os.remove(os.path.join(MEDIA_PATH, file_info['file_path']))
                except Exception as e:
                    print(e)
                return json_response(data=args)
            else:
                return json_response(code=1, message="文件已被督办事务使用，不能删除")
        else:
            return json_response(code=1, message='文件不存在')


class DownloadFileView(Resource):
    """
    下载文件
    """

    @admin_login_req
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("file_path", type=str, help='文件必填', required=True)
        args = parser.parse_args()
        try:
            file_path = os.path.join(MEDIA_PATH, args['file_path'].strip("/"))
            if os.path.exists(file_path):
                with open(file_path, mode='rb') as f:
                    content = f.read()
                rv = make_response(content)
                filename = file_path.rsplit('/')[-1].rsplit("_")[-1]
                mime_type = mimetypes.guess_type(filename)[0]
                rv.headers['Content-Type'] = mime_type
                rv.headers["Cache-Control"] = "no-cache"
                rv.headers['Content-Disposition'] = 'attachment; filename={}'.format(
                    filename.encode().decode('latin-1'))
                return rv
            else:
                return json_response(code=1, message='文件不存在')
        except Exception as err:
            import traceback
            traceback.print_exc()
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
        parser.add_argument("date", type=str, help='年月', required=True)
        args = parser.parse_args()
        result = AdminOperateModel().get_my_memo(request.user['id'], args['date'])
        return json_response(data=result)

    @admin_login_req
    def post(self):
        form = AddMemoEventForm().from_json(request.json)
        if form.validate():
            try:
                data = dict(form.data)
                data['add_time'] = datetime.datetime.now()
                data['admin_id'] = request.user['id']
                AdminModel().execute_insert(self.__table__, **data)
                return json_response(code=0, message="添加成功")
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
        memo = model.get_data_by_id(self.__table__, args['id'])
        if memo is None:
            return json_response(code=1, message="无此备忘记录")
        if memo['admin_id'] != request.user['id']:
            return json_response(code=1, message="无权限操作此备忘录")
        model.execute_delete(self.__table__, [f'id={args["id"]}', 'admin_id={}'.format(request.user['id'])])
        return json_response(code=0, message="删除成功")


class ScheduleView(Resource):
    """
    行程安排
    """

    __table__ = 'schedule_event'

    @admin_login_req
    @allow_role_req([1, 2, 3])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("user_id", type=str, help='用户id', required=False)
        parser.add_argument("date", type=str, help='年月', required=True)
        args = parser.parse_args()
        admin = request.user
        if admin['role_id'] not in [1, 2]:  # 副局长只能看自己的
            args['user_id'] = request.user['id']
        result = AdminOperateModel().get_schedule_event(request.user, args['user_id'], args['date'])
        return json_response(data=result)

    @admin_login_req
    @allow_role_req([1, 2, 3])
    def post(self):
        form = AddScheduleEventForm().from_json(request.json)
        if form.validate():
            try:
                data = dict(form.data)
                admin = request.user
                if admin['role_id'] not in [1, 2] and request.user['id'] != form.data['arranged_id']:
                    return json_response(code=1, message="无权给此人安排行程")
                data['add_time'] = datetime.datetime.now()
                data['operator_id'] = admin['id']
                model = AdminOperateModel()
                data['id'] = model.execute_insert(self.__table__, **data)
                model.insert_log(self.__table__, data['id'], "新增行程", data)
                now_time = datetime.datetime.now()
                if admin['id'] != form.data['arranged_id']:
                    send_sys_message([{"type": "行程", "status": "待签收", "send_time": now_time,
                                       "receive_id": data['arranged_id'],
                                       "title": "新安排行程：{}，请前去查看".format(data['title'])}])
                return json_response(code=0, message="行程添加成功")
            except pymysql.err.IntegrityError:
                return json_response(code=1, message="当天行程名已被使用")
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    @allow_role_req([1, 2, 3])
    def put(self):
        form = UpdateScheduleEventForm().from_json(request.json)
        if form.validate():
            try:
                data = dict(form.data)
                admin = request.user
                if admin['role_id'] not in [1, 2] and request.user['id'] != form.data['arranged_id']:
                    return json_response(code=1, message="无权修改此人安排行程")
                model = AdminOperateModel()
                schedule = model.get_data_by_id(self.__table__, data['id'])
                model.execute_update(self.__table__, data, schedule)
                model.update_log(self.__table__, data['id'], "修改行程:{}".format(data['title']), schedule, data)
                now_time = datetime.datetime.now()
                if admin['id'] != form.data['arranged_id']:
                    send_sys_message([{"type": "行程", "status": "待签收", "send_time": now_time,
                                       "receive_id": data['arranged_id'],
                                       "title": "修改行程：{}，请前去查看".format(data['title'])}])
                return json_response(message="行程修改成功")
            except pymysql.err.IntegrityError:
                return json_response(code=1, message="当天行程名已被使用")
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    @allow_role_req([1, 2, 3])
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='id', required=True)
        args = parser.parse_args()
        model = AdminOperateModel()
        schedule = model.get_data_by_id(self.__table__, args['id'])
        if schedule is None:
            return json_response(code=1, message="无此行程记录")
        admin = request.user
        if admin['role_id'] in [1, 2] and request.user['id'] != schedule['arranged_id']:
            return json_response(code=1, message="无权删除此人安排行程")
        model.execute_delete(self.__table__, [f'id={args["id"]}', 'arranged_id={}'.format(admin['id'])])
        model.delete_log(self.__table__, schedule['id'], "删除行程：{}".format(schedule['title']), schedule)
        if admin['id'] != schedule['arranged_id']:
            send_sys_message([{"type": "行程", "status": "待签收", "send_time": datetime.datetime.now(),
                               "receive_id": schedule['arranged_id'],
                               "title": "行程：{}被删除，请前去查看".format(schedule['title'])}])
        return json_response(code=0, message="删除成功")


class TaxProgressView(Resource):
    """
    税率进度
    """

    __table__ = 'tax_progress'

    @admin_login_req
    @allow_role_req([1, 2, 3, 4])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("year", type=int, help='年份必填', required=True)
        args = parser.parse_args()
        tax = AdminOperateModel().get_tax_progress(args['year'])
        return json_response(data=tax)

    @admin_login_req
    @allow_role_req([4])
    def put(self):
        if request.user['department_name'] != '财务管理科':
            return json_response(code=0, message="非财务科不能编辑")
        form = UpdateTaxProgressForm().from_json(request.json)
        if form.validate():
            tax = AdminOperateModel().replace_tax_progress(form.data)
            return json_response(data=tax)
        else:
            return json_response(code=1, errors=form.errors)


class EmployeeStatusView(Resource):
    """
    员工状态统计填写
    """

    __table__ = 'employee_status'

    @admin_login_req
    @allow_role_req([1, 2, 3, 4])
    def get(self):
        data = AdminOperateModel().get_employee_status()
        return json_response(data=data)

    @admin_login_req
    @allow_role_req([1, 2, 3, 4])
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("ltx", type=int, help='离、退休', required=True)
        parser.add_argument("gnt", type=int, help='改非、内退、退岗', required=True)
        parser.add_argument("zg", type=int, help='在岗', required=True)
        args = parser.parse_args()
        if request.user['department_name'] != '人事管理科':
            return json_response(code=0, message="非财务科不能编辑")
        model = AdminOperateModel()
        origin_data = model.get_employee_status()
        model.update_employee_status(args)
        model.update_log(self.__table__, None, "修改员工状态数据", origin_data, args)
        return json_response(data=args)


class DepartmentNoticeView(Resource):
    """
    部门通知
    """

    __table__ = 'department_notice'

    @admin_login_req
    # @allow_role_req(role_ids=[4])
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=int, help='部门id', required=False)
        parser.add_argument("title", type=str, help='标题', required=False)
        parser.add_argument("page", type=int, help='页码', required=False, default=1)
        parser.add_argument("page_size", type=int, help='每页数量', required=False, default=10)
        args = parser.parse_args()
        # args['department_id'] = request.user['department_id']
        tax = DepartmentModel().get_department_notice_list(args['department_id'], args['title'],
                                                           args['page'], args['page_size'])
        return json_response(data=tax)

    @admin_login_req
    @allow_role_req([1, 4])
    def post(self):
        form = AddDepartmentNoticeForm().from_json(request.json)
        if form.validate():
            model = DepartmentModel()
            data = dict(form.data)
            data['operator_id'] = request.user['id']
            data['department_id'] = request.user['department_id']
            data['add_time'] = datetime.datetime.now()
            notice = model.execute_insert(self.__table__, **data)
            return json_response(data=notice)
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    @allow_role_req([1, 4])
    def put(self):
        form = UpdateDepartmentNoticeForm().from_json(request.json)
        if form.validate():
            model = DepartmentModel()
            notice = model.get_data_by_id(self.__table__, form.data['id'])
            if notice['department_id'] != request.user['department_id']:
                return json_response(code=1, message="不能操作其他部门公告")
            model.execute_update(self.__table__, form.data, notice)
            return json_response(data=form.data)
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    @allow_role_req([1, 4])
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='公告id', required=False)
        args = parser.parse_args()
        model = DepartmentModel()
        notice = model.get_data_by_id(self.__table__, args['id'])
        if notice['department_id'] != request.user['department_id']:
            return json_response(code=1, message="不能操作其他部门公告")
        model.execute_delete(self.__table__, ['id={}'.format(args['id'])])
        return json_response(data=notice)
