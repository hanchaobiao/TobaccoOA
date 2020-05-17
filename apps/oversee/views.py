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
from apps.oversee.forms import AddOverseeTaskForm, UpdateOverseeTaskForm, SubmitOverseeTaskForm, AuditOverseeTaskForm,\
    OverseeMessageForm
from module.OverseeTaskDb import OverseeTaskModel
from module.AdminDb import AdminModel
from common.response import json_response
from apps.utils.db_transaction import db_transaction
from apps.utils.jwt_login_decorators import admin_login_req
from resources.redis_pool import RedisPool


class ReleaseOverseeTaskView(Resource):
    """
    发布任务
    """

    __table__ = 'oversee_task'  # 操作表
    __table_desc__ = '督办任务'

    @staticmethod
    @admin_login_req
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=str, help='任务名称', required=False, default=None)
        parser.add_argument("name", type=str, help='任务名称', required=False, default=None)
        parser.add_argument("type", type=str, help='任务状态', choices=['重大任务', '专项任务', '普通任务'], required=False,
                            default=None)
        parser.add_argument("relation", type=str, help='任务关系', required=False, default=None)
        parser.add_argument("page", type=int, help='页码', required=False, default=1)
        parser.add_argument("page_size", type=int, help='页数', required=False, default=20)
        args = parser.parse_args()
        model = OverseeTaskModel()
        if args.get("id"):
            result = model.get_oversee_task_detail(args['id'])
        else:
            result = model.get_oversee_task_list(request.user, args['name'], args['type'], args['relation'],
                                                 args['page'], args['page_size'])
            if len(result['list']):
                ids = model.get_all_people_ids(result['list'])
                admin_list = AdminModel().get_admin_by_ids(ids)
                result['list'] = model.convert_real_name(result['list'], admin_list)
        return json_response(data=result)

    @admin_login_req
    def post(self):
        form = AddOverseeTaskForm().from_json(request.json)
        if form.validate():
            data = dict(form.data)
            data['add_time'] = datetime.datetime.now()
            task_detail_list = data.pop("oversee_details")
            model = OverseeTaskModel()
            model.set_autocommit(0)
            try:
                file_ids = data.pop("file_ids")
                data['release_id'] = request.user['id']
                task = model.execute_insert(self.__table__, data)
                file_list = [{"file_id": file_id, "task_id": task['id']} for file_id in file_ids]
                model.execute_insert_many('rel_task_file', file_list)
                model.insert_log(self.__table__, task['id'], '发布督办任务：{}'.format(task['name']), task)
                for index, task_detail in enumerate(task_detail_list):
                    coordinator_ids = task_detail.pop("coordinator_ids")
                    task_detail = model.add_oversee_task_detail(task['id'], task_detail)
                    self.insert_log('oversee_task_detail', task_detail['id'],
                                    '督办任务：{}子任务：{}'.format(task['name'], index+1), task_detail,
                                    [{"name": "coordinator_ids", "desc": "协办人", "value": str(coordinator_ids)}])
                    for coordinator_id in coordinator_ids:
                        model.add_task_coordinator(task['id'], task_detail['id'], coordinator_id)
                    model.conn.commit()
                    model.set_autocommit(1)
                    return json_response(message="添加成功")
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()
                model.conn.rollback()
                model.set_autocommit(1)
                return json_response(code="FAIL", message="添加失败", data={})
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    def put(self):
        form = UpdateOverseeTaskForm().from_json(request.json)
        if form.validate():
            task = dict(form.data)
            task_detail_list = task.pop("oversee_details")
            model = OverseeTaskModel()
            model.set_autocommit(0)
            try:
                task['file_names'] = str(task['file_names'])
                oversee_task = model.get_data_by_id(self.__table__, task['id'])
                count = model.execute_update(self.__table__, task, oversee_task)
                if count:
                    self.update_log(self.__table__, task['id'], '修改督办任务：{}'.format(task['name']),
                                    oversee_task, task)
                for index, update_data_detail in enumerate(task_detail_list):
                    task_detail = model.get_data_by_id('oversee_task_detail', update_data_detail['id'])
                    count = model.execute_update('oversee_task_detail', update_data_detail, task_detail,
                                                 extra_conditions=['status = "待提交"'])
                    if count:
                        model.update_log('oversee_task_detail', task_detail['id'], '修改督办任务：{}子任务：{}'.format(
                            task['name'], index + 1), task_detail, update_data_detail)
                    model.conn.commit()
                    model.set_autocommit(1)
                    return json_response(message="修改成功")
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()
                model.conn.rollback()
                model.set_autocommit(1)
                return json_response(code="FAIL", message="修改失败", data={})
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='任务id', required=True)
        args = parser.parse_args()
        model = OverseeTaskModel()
        try:
            task = model.get_data_by_id(self.__table__, args['id'])
            if task:
                model.set_autocommit(0)
                model.delete_task(args['id'])
                model.delete_log(self.__table__, args['id'], "删除任务：{}".format(task['name']), task)
                model.set_autocommit(1)
            else:
                pass
            return json_response(message="删除")
        except Exception as e:
            print(e)
            import traceback
            traceback.print_exc()
            model.conn.rollback()
            model.set_autocommit(1)
            return json_response(code="FAIL", message="修改失败", data={})


class SubmitOverseeTaskView(Resource):

    __table__ = 'oversee_task_detail'  # 操作表
    __table_desc__ = '提交任务'

    @staticmethod
    def allowed_file(filename):
        if filename.split(".")[-1] not in ["jpg", "jpeg", "png", "gif", "doc", "docx", "xls", "xlsx", "pdf"]:
            return False
        return True

    @admin_login_req
    def put(self):
        form = SubmitOverseeTaskForm().from_json(request.values.to_dict())
        if form.validate():
            update_data = dict(form.data)
            delete_file_ids = update_data.pop("delete_file_ids")
            model = OverseeTaskModel()
            task_detail = model.get_task_detail_and_task_name_by_id(update_data['id'])
            if task_detail['agent_id'] == request.user['id']:
                return json_response(code=1, message="无权限操作该任务")
            if task_detail['status'] == '已完成':
                return json_response(code=1, message="任务已结束，不能修改")
            situation = model.before_task_complete_situation(task_detail)
            if situation['unfinished_num'] > 0:
                return json_response(code=1, message="前面任务尚未完成，暂时不能提交")
            try:
                model.set_autocommit(0)
                update_data['status'] = '待审核'
                update_data['submit_time'] = datetime.datetime.now()
                model.execute_update(self.__table__, update_data, extra_conditions=['status!="已完成"'])
                message = '经办人：{}提交任务:{}->子任务：{}'.format(request.user['real_name'], task_detail['name'],
                                                         situation['index'])
                model.update_log(self.__table__, update_data['id'], message, task_detail, update_data)
                # 删除文件
                model.delete_file_by_ids(update_data['id'], delete_file_ids)
                for f in request.files.getlist('file'):
                    file_info = dict()
                    # 检查文件类型
                    now_time = datetime.datetime.now()
                    file_info['file_name'] = f.filename
                    file_info['size'] = len(f.read())
                    file_info['task_detail_id'] = task_detail['id']
                    file_info['task_id'] = task_detail['task_id']
                    if f and self.allowed_file(f.filename):
                        new_filename = str(now_time).replace(" ", '-') + '_' + f.filename
                        base_bath = os.path.join(MEDIA_PATH, now_time.strftime('%Y%m'))
                        if os.path.exists(base_bath) is False:
                            os.mkdir(base_bath)
                        file_path = os.path.join(base_bath, new_filename)
                        f.save(file_path)
                        file_info['add_time'] = now_time
                        file_info['file_path'] = file_path.replace(MEDIA_PATH, '')
                        file_info['id'] = model.execute_insert('oversee_task_detail_file', **file_info)
                        model.insert_log(self.__table__, file_info['id'], "上传任务文件：{}".format(f.filename), file_info)
                model.conn.commit()
                model.set_autocommit(1)
                return json_response(code=0, message="提交成功")
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()
                model.conn.rollback()
                model.set_autocommit(1)
                return json_response(code="FAIL", message="修改失败", data={})
        else:
            return json_response(code=1, errors=form.errors)


class AuditOverseeTaskView(Resource):

    __table__ = 'oversee_task_detail'  # 操作表
    __table_desc__ = '提交任务'

    @admin_login_req
    def put(self):
        form = AuditOverseeTaskForm().from_json(request.json)
        if form.validate():
            update_data = dict(form.data)
            model = OverseeTaskModel()
            task_detail = model.get_task_detail_and_task_name_by_id(update_data['id'])
            if task_detail['status'] not in ['待审核', '审批拒绝', '任务完成']:
                return json_response(code=1, message="任务无法审批")
            if task_detail['oversee_id'] == request.user['id']:
                return json_response(code=1, message="无权限操作该任务")
            situation = model.before_task_complete_situation(task_detail)
            if situation['unfinished_num'] > 0:
                return json_response(code=1, message="前面任务尚未完成，暂时不能提交")
            try:
                model.set_autocommit(0)
                update_data['audit_time'] = datetime.datetime.now()
                count = model.execute_update(self.__table__, update_data, task_detail,
                                             {"audit_time": datetime.datetime.now()},
                                             extra_conditions=['status!="%s"' % '待提交'])
                if count:
                    message = '督办人：{}提交任务:{}->子任务：{}'.format(request.user['real_name'], task_detail['name'],
                                                             situation['index'])
                    model.update_task_progress(task_detail['task_id'])
                    model.update_log(self.__table__, update_data['id'], message, task_detail, update_data)
                    result = {"code": 0, "message": "审批成功"}
                else:
                    result = {"code": 1, "message": "数据未发生变化"}
                model.conn.commit()
                model.set_autocommit(1)
                return json_response(**result)
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()
                model.conn.rollback()
                model.set_autocommit(1)
                return json_response(code="FAIL", message="修改失败", data={})
        else:
            return json_response(code=1, errors=form.errors)


class OverseeMessageTaskView(Resource):

    __table__ = 'oversee_message'  # 操作表
    __table_desc__ = '督办消息'

    @staticmethod
    @admin_login_req
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("type", type=str, help='消息类型', choices=['send', 'receive'], required=False)
        parser.add_argument("page", type=int, help='页码', required=False, default=1)
        parser.add_argument("page_size", type=int, help='页数', required=False, default=10)
        args = parser.parse_args()
        model = OverseeTaskModel()
        result = model.get_oversee_message_list(request.user, args['type'], args['page'], args['page_size'])
        return json_response(data=result)

    @admin_login_req
    def post(self):
        form = OverseeMessageForm().from_json(request.json)
        if form.validate():
            update_data = dict(form.data)
            model = OverseeTaskModel()
            task_detail = model.get_task_detail_and_task_name_by_id(update_data['id'])
            if task_detail['status'] not in ['待提交', '审批拒绝']:
                return json_response(code=1, message="当前任务状态，无需督办")
            if task_detail['oversee_id'] == request.user['id']:
                return json_response(code=1, message="无权限操作该任务")
            update_data['agent_id'] = task_detail['agent_id']
            update_data['oversee_id'] = task_detail['oversee_id']
            update_data['send_time'] = datetime.datetime.now()
            update_data['title'] = "尽快完成任务：{}".format(task_detail['name'])
            model.execute_insert(self.__table__, **update_data)
            return json_response(code=0, message="督办消息已发送")

    @admin_login_req
    def post(self):
        form = OverseeMessageForm().from_json(request.json)
        if form.validate():
            update_data = dict(form.data)
            model = OverseeTaskModel()
            task_detail = model.get_task_detail_and_task_name_by_id(update_data['task_detail_id'])
            if task_detail['status'] not in ['待提交', '审批拒绝']:
                return json_response(code=1, message="当前任务状态，无需督办")
            update_data['agent_id'] = task_detail['agent_id']
            update_data['oversee_id'] = task_detail['oversee_id']
            update_data['send_time'] = datetime.datetime.now()
            update_data['title'] = "尽快完成任务：{}".format(task_detail['name'])
            model.execute_insert(self.__table__, **update_data)
            return json_response(code=0, message="督办消息已发送")

    @admin_login_req
    def put(self):
        message_id = request.json['id']
        model = OverseeTaskModel()
        update_data = {"id": message_id, "receive_time": datetime.datetime.now()}
        count = model.execute_update(self.__table__, update_data,
                                     extra_conditions=[f'agent_id={request.user["id"]}', 'receive_time is null'])
        if count == 1:
            return json_response(code=0, message="状态修改成功")
        return json_response(code=1, message="状态修改失败")
