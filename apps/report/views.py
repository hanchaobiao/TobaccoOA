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


class EmployeeReportView(Resource):
    """
    员工统计
    """

    __table_desc__ = '心愿'

    @admin_login_req
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=int, help='部门id', required=False, default=None)
        args = parser.parse_args()
        model = ReportModel()
        result = model.get_employee_status(args['department_id'])
        return json_response(data=result)


