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
from apps.wish.forms import AddWishForm, UpdateWishForm, AuditWishForm, SubmitWishForm, EvaluationWishForm
from module.OverseeTaskDb import OverseeTaskModel
from module.WishDb import WishModel
from common.response import json_response
from apps.utils.db_transaction import db_transaction
from apps.utils.jwt_login_decorators import admin_login_req
from apps.utils.permissions_auth import allow_role_req
from resources.redis_pool import RedisPool
from apps.admin_operation.task import upload_file
from apps.oversee.task import send_sys_message


class AuditWishView(Resource):
    """
    心愿
    """

    __table__ = 'employee_wish'  # 操作表
    __table_desc__ = '心愿'

    @admin_login_req
    @allow_role_req([1])
    def put(self):
        form = AuditWishForm().from_json(request.json)
        if form.validate():
            audit_data = dict(form.data)
            audit_data['audit_time'] = datetime.datetime.now()
            if audit_data['status'] == '待签收':
                if (audit_data['department_id'] and audit_data['agent_id']) is False:
                    return json_response(code=1, message="审批通过，请选择经办人")
            model = WishModel()
            wish = model.get_data_by_id(self.__table__, audit_data['id'])
            if wish['status'] not in ['待审核', '待签收']:
                return json_response(code=1, message="该任务无法重新审核")
            count = model.execute_update(self.__table__, audit_data, wish)
            if count:
                model.update_log(self.__table__, wish['id'], '审核心愿：{}'.format(wish['name']), wish, audit_data)
                message = None
                if audit_data['status'] == '待签收':
                    message = {"type": "心愿", "send_time": datetime.datetime.now(), "wish_id": wish['id'],
                               "receive_id": audit_data['agent_id'], "status": audit_data['status'],
                               "title": "员工心愿：{}待签收".format(wish['name'])}
                elif wish['status'] == '待签收' and audit_data['status'] == '驳回':
                    message = {"type": "心愿", "send_time": datetime.datetime.now(), "wish_id": wish['id'],
                               "receive_id": audit_data['agent_id'], "status": "驳回",
                               "title": "员工心愿：{}被驳回，不需要办理".format(wish['name'])}
                if message:
                    send_sys_message([message])
            return json_response(data=audit_data, message="审核成功")
        else:
            return json_response(code=1, errors=form.errors)


class EmployeeWishView(Resource):
    """
    心愿
    """

    __table__ = 'employee_wish'  # 操作表
    __table_desc__ = '心愿'

    @admin_login_req
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, help='心愿id', required=False, default=None)
        parser.add_argument("name", type=str, help='任务名称', required=False, default=None)
        parser.add_argument("status", type=str, help='执行状态', choices=['', '待审核', '驳回', '待签收', '待提交', '心愿完成'],
                            required=False, default=None)
        parser.add_argument("page", type=int, help='页码', required=False, default=1)
        parser.add_argument("page_size", type=int, help='页数', required=False, default=20)
        args = parser.parse_args()
        model = WishModel()
        if args['id']:
            result = model.get_employee_wish_detail(request.user, args['id'])
        else:
            result = model.get_employee_wish_list(request.user, args['name'], args['status'],
                                                  args['page'], args['page_size'])
        return json_response(data=result)

    @admin_login_req
    def post(self):
        form = AddWishForm().from_json(request.values.to_dict())
        if form.validate():
            data = dict(form.data)
            data['add_time'] = datetime.datetime.now()
            data['status'] = '待审核'
            data['employee_id'] = request.user['id']
            model = WishModel()
            data['id'] = model.execute_insert(self.__table__, **data)
            file_list = upload_file('wish', wish_id=data['id'], file_type=1)
            model.execute_insert_many('employee_wish_file', file_list)
            model.insert_log(self.__table__, data['id'], '发布心愿：{}'.format(data['name']))
            return json_response(data=data, message="添加成功")
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    def put(self):
        form = UpdateWishForm().from_json(request.values.to_dict())
        if form.validate():
            update_data = dict(form.data)
            model = WishModel()
            wish = model.get_data_by_id(self.__table__, form.data['id'])
            if wish['employee_id'] != request.user['id']:
                return json_response(code=1, message="该心愿无权操作")
            if wish['status'] != '待审核':
                return json_response(code=1, message="该心愿已经审核，无法修改")
            file_ids = update_data.pop("file_ids")
            model.execute_update(self.__table__, update_data, wish)
            file_list = upload_file('wish', wish_id=wish['id'], file_type=1)
            model.reset_wish_file(wish['id'], file_ids)
            model.update_log(self.__table__, wish['id'], '修改心愿：{}'.format(update_data['name']), wish, update_data)
            return json_response(data=update_data, message="修改成功")
        else:
            return json_response(code=1, errors=form.errors)

    @admin_login_req
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=str, help='心愿id', required=False, default=None)
        args = parser.parse_args()
        model = WishModel()
        wish = model.get_data_by_id(self.__table__, args['id'])
        if wish['employee_id'] != request.user['id']:
            return json_response(code=1, message="无权限删除该心愿")
        if wish['status'] != '待审核':
            return json_response(code=1, message="该心愿已经审核，无法删除")
        model.execute_delete('employee_wish_file', [f'wish_id={wish["id"]}'])
        model.execute_delete(self.__table__, ['id={}'.format(wish['id'])])
        return json_response(data={}, message="删除成功")


class EvaluationWishView(Resource):
    """
    心愿申诉
    """

    __table__ = 'employee_wish'  # 操作表

    @admin_login_req
    def put(self):
        form = EvaluationWishForm().from_json(request.json)
        if form.validate():
            data = dict(form.data)
            data['feedback_time'] = datetime.datetime.now()
            model = WishModel()
            wish = model.get_data_by_id(self.__table__, data['id'])
            if wish['status'] != '心愿完成':
                return json_response(code=1, message="心愿尚未完成，无法申诉，点赞")
            if wish['agent_id'] != request.user['id']:
                return json_response(code=1, message="无权限评价该心愿")
            data['id'] = model.execute_update(self.__table__, data, wish)
            model.update_log(self.__table__, data['id'], '评价心愿：{}'.format(wish['name']), wish, data)
            return json_response(data=data, message="评价成功")


class SubmitWishView(Resource):
    """
    提交心愿
    """

    __table__ = 'employee_wish'  # 操作表
    __table_desc__ = '心愿'

    @admin_login_req
    def post(self):
        wish_id = request.json['id']
        model = WishModel()
        wish = model.get_data_by_id(self.__table__, wish_id)
        if wish['status'] != '待签收':
            return json_response(code=1, message="改状态无法签收")
        if wish['agent_id'] != request.user['id']:
            return json_response(code=1, message="无权限签收该心愿")
        update_data = {"id": wish_id, "status": "待提交", "receive_time": datetime.datetime.now()}
        model.execute_update(self.__table__, update_data, wish)
        return json_response(data={}, message="签收成功")

    @admin_login_req
    def put(self):
        form = SubmitWishForm().from_json(request.values.to_dict())
        if form.validate():
            data = dict(form.data)
            data['submit_time'] = datetime.datetime.now()
            data['status'] = '心愿完成'
            model = WishModel()
            try:
                model.start_transaction()
                wish = model.get_data_by_id(self.__table__, data['id'])
                if wish['status'] != '待提交':
                    return json_response(code=1, message="改状态无法提交结果")
                if wish['agent_id'] != request.user['id']:
                    return json_response(code=1, message="无权限经办该心愿")
                data['id'] = model.execute_update(self.__table__, data, wish)
                file_list = upload_file('wish', wish_id=data['id'], file_type=2)
                model.execute_insert_many('employee_wish_file', file_list)
                model.update_log(self.__table__, data['id'], '经办心愿：{}上传完成信息'.format(wish['name']), wish, data)
                model.conn.commit()
                return json_response(data=data, message="心愿办理资料提交成功")
            except Exception as e:
                print(e)
                model.conn.rollback()
                return json_response(data=data, message="心愿办理资料提交失败")
        else:
            return json_response(code=1, errors=form.errors)

