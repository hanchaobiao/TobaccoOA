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
from module.ReportDb import ReportModel
from common.response import json_response
from apps.utils.db_transaction import db_transaction
from apps.utils.jwt_login_decorators import admin_login_req
from resources.redis_pool import RedisPool
from apps.admin_operation.task import upload_file
from apps.oversee.task import send_sys_message


class EmployeeStatusReportView(Resource):
    """
    员工状态统计
    """

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=int, help='部门id', required=False, default=2)
        args = parser.parse_args()
        model = ReportModel()
        result = model.get_employee_status(args['department_id'])
        return json_response(data=result)


class LeaderRateView(Resource):
    """
    领导分布
    """

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=int, help='部门id', required=False, default=2)
        args = parser.parse_args()
        model = ReportModel()
        result = model.get_leader_statistics(args['department_id'])
        return json_response(data=result)


class TaskCompleteSituationView(Resource):
    """
    任务完成情况
    """

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=int, help='部门id', required=False, default=2)
        args = parser.parse_args()
        model = ReportModel()
        result = model.oversee_task_statistics(args['department_id'])
        return json_response(data=result)


class TaskTrendView(Resource):
    """
    任务趋势
    """

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=int, help='部门id', required=False, default=2)
        args = parser.parse_args()
        model = ReportModel()
        result = model.oversee_task_trend(args['department_id'])
        return json_response(data=result)


class TaxShowView(Resource):
    """
    税率
    """

    @staticmethod
    def get():
        model = ReportModel()
        result = model.get_newest_tax()
        return json_response(data=result)
