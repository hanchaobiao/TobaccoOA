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
from apps.utils.permissions_auth import allow_role_req
from resources.redis_pool import RedisPool
from apps.oversee.task import send_sys_message
from apps.admin_operation.task import upload_file


class ReleaseOverseeTaskView(Resource):
    """
    发布任务
    """

    __table__ = 'oversee_task'  # 操作表
    __table_desc__ = '督办任务'

    @staticmethod
    @admin_login_req
    @allow_role_req([1, 2, 3, 4])
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=str, help='任务名称', required=False, default=None)
        parser.add_argument("name", type=str, help='任务名称', required=False, default=None)
        parser.add_argument("status", type=str, help='执行状态', choices=['', '待签收', '待审核', '审核拒绝', '已完成'],
                            required=False, default=None)
        parser.add_argument("type", type=str, help='任务类型', choices=['', '重大任务', '专项任务', '普通任务', '常规状态'],
                            required=False, default=None)
        parser.add_argument("relation", type=str, help='任务关系', choices=['', '由我发布', '由我经办', '由我督办', '由我协办'],
                            required=False, default=None)
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
    @allow_role_req([1])
    def post(self):
        form = AddOverseeTaskForm().from_json(request.json)
        if form.validate():
            task = dict(form.data)
            task['status'] = '待签收'
            task['add_time'] = datetime.datetime.now()
            task_detail_list = task.pop("oversee_details")
            model = OverseeTaskModel()
            try:
                model.start_transaction()
                oversee_messages = []
                file_ids = list(set(task.pop("file_ids")))
                task['release_id'] = request.user['id']
                task['task_no'] = model.generate_task_no(task['type'])
                task['id'] = model.execute_insert(self.__table__, **task)
                file_list = [{"file_id": file_id, "task_id": task['id']} for file_id in file_ids]
                model.execute_insert_many('rel_task_file', file_list)
                now_time = datetime.datetime.now()
                oversee_messages.append({"type": "督办任务", "status": "待签收", "send_time": now_time, "task_id": task['id'],
                                         "receive_id": task['oversee_id'], "task_detail_id": None,
                                         "title": "督办任务：{}待签收".format(task['name'])})
                model.insert_log(self.__table__, task['id'], '发布督办任务：{}'.format(task['name']), task)
                for index, task_detail in enumerate(task_detail_list):
                    if index > 0 and task_detail['start_time'] < task_detail_list[index-1]['end_time']:
                        return json_response(code=1, message="下一任务的开始时间要大于等于前一任务的结束时间")
                    coordinator_ids = task_detail.pop("coordinator_ids")
                    task_detail = model.add_oversee_task_detail(task['id'], task_detail)
                    oversee_messages.append({"type": "经办任务", "status": "待签收", "send_time": now_time,
                                             "task_id": task['id'],
                                             "receive_id": task_detail['agent_id'], "task_detail_id": task_detail['id'],
                                             "title": "经办任务：{}->第{}阶段任务待签收".format(task['name'], index+1)})
                    model.insert_log('oversee_task_detail', task_detail['id'],
                                     '经办任务：{}子任务：{}'.format(task['name'], index+1), task_detail,
                                     [{"name": "coordinator_ids", "desc": "协办人", "value": str(coordinator_ids)}])
                    for coordinator_id in coordinator_ids:
                        model.add_task_coordinator(task['id'], task_detail['id'], coordinator_id)
                send_sys_message(oversee_messages)
                model.conn.commit()
                return json_response(message="添加成功")
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()
                model.conn.rollback()
                return json_response(code="FAIL", message="添加失败", data={})
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    @allow_role_req([1])
    def put(self):
        form = UpdateOverseeTaskForm().from_json(request.json)
        if form.validate():
            task = dict(form.data)
            task_detail_list = task.pop("oversee_details")
            model = OverseeTaskModel()
            oversee_messages = []
            try:
                model.start_transaction()
                file_ids = list(set(task.pop("file_ids")))
                oversee_task = model.get_data_by_id(self.__table__, task['id'])
                count = model.execute_update(self.__table__, task, oversee_task)
                now_time = datetime.datetime.now()
                if count:
                    model.update_log(self.__table__, task['id'], '修改督办任务：{}'.format(task['name']),
                                     oversee_task, task)

                    if task['oversee_id'] == oversee_task['oversee_id']:
                        oversee_messages.append({"type": "督办任务", "status": "待签收", "send_time": now_time,
                                                 "task_id": task['id'], "receive_id": task['oversee_id'],
                                                 "title": "督办任务：{}发生变更，请尽快查看".format(task['name'])})
                    else:
                        oversee_messages.append({"type": "督办任务", "status": "待签收", "send_time": now_time,
                                                 "task_id": task['id'], "receive_id": task['oversee_id'],
                                                 "title": "督办任务：{}待签收".format(task['name'])})
                        oversee_messages.append({"type": "督办任务", "status": "待签收", "send_time": now_time,
                                                 "task_id": task['id'], "receive_id": oversee_task['oversee_id'],
                                                 "title": "督办任务：{}已改由他人督办，请知晓".format(task['name'])})

                model.reset_rel_task_file(task['id'], file_ids)
                for index, update_data_detail in enumerate(task_detail_list):
                    coordinator_ids = update_data_detail.pop("coordinator_ids")
                    task_detail = model.get_data_by_id('oversee_task_detail', update_data_detail['id'])
                    if task_detail['status'] not in ("待签收", "待提交"):
                        continue
                    count = model.execute_update('oversee_task_detail', update_data_detail, task_detail)
                    model.reset_coordinator_ids(task['id'], task_detail['id'], coordinator_ids)
                    if count:

                        if task_detail['agent_id'] == update_data_detail['agent_id']:
                            oversee_messages.append({
                                "type": "经办任务", "status": "待签收", "send_time": now_time, "task_id": task['id'],
                                "receive_id": task_detail['agent_id'], "task_detail_id": task_detail['id'],
                                "title": "经办任务：{}->第{}阶段任务发生变更，请尽快查看".format(task['name'], index + 1)})
                        else:
                            oversee_messages.append({
                                "type": "经办任务", "status": "待签收", "send_time": now_time, "task_id": task['id'],
                                "receive_id": task_detail['agent_id'], "task_detail_id": task_detail['id'],
                                "title": "经办任务：{}->第{}阶段任务已改由他人经办，请知晓".format(task['name'], index + 1)})
                            oversee_messages.append({
                                "type": "经办任务", "status": "待签收", "send_time": now_time, "task_id": task['id'],
                                "receive_id": update_data_detail['agent_id'], "task_detail_id": task_detail['id'],
                                "title": "经办任务：{}->第{}阶段任务待签收".format(task['name'], index + 1)})

                        model.update_log('oversee_task_detail', task_detail['id'], '修改经办任务：{}子任务：{}'.format(
                            task['name'], index + 1), task_detail, update_data_detail)
                    send_sys_message(oversee_messages)
                    model.conn.commit()
                    return json_response(message="修改成功")
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()
                model.conn.rollback()
                return json_response(code="FAIL", message="修改失败", data={})
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    @allow_role_req([1])
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='任务id', required=True)
        args = parser.parse_args()
        model = OverseeTaskModel()
        try:
            oversee_messages = []
            task = model.get_data_by_id(self.__table__, args['id'])
            now_time = datetime.datetime.now()
            if task:
                model.start_transaction()
                result = model.delete_task(args['id'])
                if result['code'] == 0:
                    oversee_messages.append({
                        "type": "督办任务", "status": "待签收", "send_time": now_time, "task_id": task['id'],
                        "receive_id": task['oversee_id'], "task_detail_id": None,
                        "title": "督办任务：{}->已取消，请知晓".format(task['name'])})
                    for task_detail in result.pop("task_details"):
                        oversee_messages.append({
                            "type": "经办任务", "status": "待签收", "send_time": now_time, "task_id": task['id'],
                            "receive_id": task_detail['agent_id'], "task_detail_id": task_detail['id'],
                            "title": "经办任务：{}->已取消，请知晓".format(task['name'])})
                    send_sys_message(oversee_messages)
                    model.delete_log(self.__table__, args['id'], "删除任务：{}".format(task['name']), task)
                model.conn.commit()
                return json_response(**result)
            else:
                return json_response(code=1, message="任务不存在")
        except Exception as e:
            print(e)
            import traceback
            traceback.print_exc()
            model.conn.rollback()
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
    # @allow_role_req([4])
    def post(self):
        """
        签收任务
        :return:
        """
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='签收子任务id', required=False, default=None)
        args = parser.parse_args()
        model = OverseeTaskModel()
        task_detail = model.get_task_detail_and_task_name_by_id(args['id'])
        if task_detail['status'] != '待签收':
            return json_response(code=1, message="当前状态无法签收")
        args['status'] = '待提交'
        datetime.datetime.now()
        model.execute_update(self.__table__, args)
        model.update_log(self.__table__, args['id'], "签收任务：%s" % task_detail['name'], task_detail, args)
        return json_response(code=0, message="签收成功")

    @admin_login_req
    # @allow_role_req([4])
    def put(self):
        form = SubmitOverseeTaskForm().from_json(request.values.to_dict())
        if form.validate():
            update_data = dict(form.data)
            file_ids = update_data.pop("file_ids")
            model = OverseeTaskModel()
            task_detail = model.get_task_detail_and_task_name_by_id(update_data['id'])
            if task_detail['agent_id'] != request.user['id']:
                return json_response(code=1, message="无权限操作该任务")
            if task_detail['status'] != '待提交':
                return json_response(code=1, message="任务状态无法提交")
            situation = model.before_task_complete_situation(task_detail)
            if situation['unfinished_num'] > 0:
                return json_response(code=1, message="前面任务尚未完成，暂时不能提交")
            try:
                model.start_transaction()
                update_data['status'] = '待审核'
                update_data['submit_time'] = datetime.datetime.now()
                model.execute_update(self.__table__, update_data, extra_conditions=['status!="已完成"'])
                message = '经办人：{}提交任务:{}->子任务：{}'.format(request.user['real_name'], task_detail['name'],
                                                         situation['index'])
                oversee_messages = [
                    {"type": "督办任务", "status": "待审核", "send_time": datetime.datetime.now(),
                     "task_id": task_detail['task_id'],
                     "receive_id": task_detail['oversee_id'], "task_detail_id": task_detail['id'],
                     "title": "督办任务：{}->第{}阶段任务待审核".format(task_detail['name'], situation['index'])}]
                model.update_log(self.__table__, update_data['id'], message, task_detail, update_data)
                # 删除文件
                model.delete_file_by_ids(update_data['id'], file_ids)
                result = upload_file('oversee', task_id=task_detail['task_id'], task_detail_id=task_detail['id'])
                if result['code'] == 1:
                    return json_response(**result)
                model.execute_insert_many('oversee_task_detail_file', result['data'])
                send_sys_message(oversee_messages)
                model.conn.commit()
                return json_response(code=0, message="经办成功")
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()
                model.conn.rollback()
                return json_response(code="FAIL", message="经办失败", data={})
        else:
            return json_response(code=1, errors=form.errors)


class AuditOverseeTaskView(Resource):

    __table__ = 'oversee_task_detail'  # 操作表
    __table_desc__ = '提交任务'

    @admin_login_req
    # @allow_role_req([1, 2, 3])
    def post(self):
        """
        签收任务
        :return:
        """
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='签收子任务id', required=False, default=None)
        args = parser.parse_args()
        model = OverseeTaskModel()
        task = model.get_data_by_id('oversee_task', args['id'])
        if task['status'] != '待签收':
            return json_response(code=1, message="当前状态无法签收")
        args['status'] = '进行中'
        model.execute_update('oversee_task', args)
        model.update_log('oversee_task', args['id'], "签收任务：%s" % task['name'], task, args)
        return json_response(code=0, message="签收成功")

    @admin_login_req
    # @allow_role_req([1, 2, 3])
    def put(self):
        form = AuditOverseeTaskForm().from_json(request.json)
        if form.validate():
            update_data = dict(form.data)
            model = OverseeTaskModel()
            task_detail = model.get_task_detail_and_task_name_by_id(update_data['id'])
            if task_detail['status'] not in ['待审核', '审核驳回', '任务完成']:
                return json_response(code=1, message="任务无法审批")
            if task_detail['oversee_id'] != request.user['id']:
                return json_response(code=1, message="无权限操作该任务")
            situation = model.before_task_complete_situation(task_detail)
            if situation['unfinished_num'] > 0:
                return json_response(code=1, message="前面任务尚未完成，暂时不能提交")
            try:
                model.start_transaction()
                update_data['audit_time'] = datetime.datetime.now()
                count = model.execute_update(self.__table__, update_data, task_detail,
                                             {"audit_time": datetime.datetime.now()},
                                             extra_conditions=['status!="%s"' % update_data['status']])
                if count:
                    message = '督办人：{}审核任务:{}->子任务：{}'.format(request.user['real_name'], task_detail['name'],
                                                             situation['index'])
                    oversee_messages = [
                        {"type": "经办任务", "status": update_data['status'], "send_time": datetime.datetime.now(),
                         "task_id": task_detail['task_id'], "task_detail_id": task_detail['id'],
                         "receive_id": task_detail['agent_id'],
                         "title": "经办任务：{}->第{}阶段任务审核结果：{}".format(task_detail['name'], situation['index'],
                                                              update_data['status'])}]
                    model.update_task_progress(task_detail['task_id'])
                    send_sys_message(oversee_messages)
                    model.update_log(self.__table__, update_data['id'], message, task_detail, update_data)
                    result = {"code": 0, "message": "审批成功"}
                else:
                    result = {"code": 1, "message": "数据未发生变化"}
                model.conn.commit()
                return json_response(**result)
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()
                model.conn.rollback()
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
        parser.add_argument("only_unread", type=int, help='仅未读', required=False, default=1)
        parser.add_argument("page", type=int, help='页码', required=False, default=1)
        parser.add_argument("page_size", type=int, help='页数', required=False, default=10)
        args = parser.parse_args()
        model = OverseeTaskModel()
        result = model.get_oversee_message_list(request.user, args['only_unread'], args['page'], args['page_size'])
        return json_response(data=result)

    @admin_login_req
    def post(self):
        form = OverseeMessageForm().from_json(request.json)
        if form.validate():
            update_data = dict(form.data)
            model = OverseeTaskModel()
            task_detail = model.get_task_detail_and_task_name_by_id(update_data['id'])
            if task_detail['status'] not in ['待签收', '待提交', '审批拒绝']:
                return json_response(code=1, message="当前任务状态，无需督办")
            if task_detail['oversee_id'] != request.user['id']:
                return json_response(code=1, message="无权限操作该任务")
            update_data['receive_id'] = task_detail['agent_id']
            update_data['send_time'] = datetime.datetime.now()
            update_data['title'] = "尽快完成任务：{}".format(task_detail['name'])
            send_sys_message([update_data])
            return json_response(code=0, message="督办消息已发送")

    @admin_login_req
    def put(self):
        message_id = request.json['id']
        model = OverseeTaskModel()
        update_data = {"id": message_id, "receive_time": datetime.datetime.now()}
        count = model.execute_update(self.__table__, update_data,
                                     extra_conditions=[f'receive_id={request.user["id"]}', 'receive_time is null'])
        return json_response(code=0, message="消息已读")
