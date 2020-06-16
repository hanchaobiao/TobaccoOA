# -*- coding: utf-8 -*-
# @Time    : 2019/4/28 19:55
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : views.py
# @Software: PyCharm

from flask_restful import Resource, reqparse
from module.ReportDb import ReportModel
from common.response import json_response


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
    任务完成情况，饼图
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


class TaskTypeCompleteSituationView(Resource):
    """
    事务分类完成情况,tab页
    """

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=int, help='部门id', required=False, default=2)
        args = parser.parse_args()
        model = ReportModel()
        result = model.oversee_type_complete_situation(args['department_id'])
        return json_response(data=result)


class YearImportantTaskView(Resource):
    """
    重大事务滚动列表
    """

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=str, help='时间', required=False, default=2)
        parser.add_argument("year", type=str, help='月份', required=False)
        parser.add_argument("month", type=str, help='年份', required=False)
        args = parser.parse_args()
        model = ReportModel()
        result = model.year_important_task(args['department_id'], args['year'], args['month'])
        return json_response(data=result)




class TaskDepartmentSortView(Resource):
    """
    部门任务完成排名
    """

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("date", type=str, help='时间', required=False)
        args = parser.parse_args()
        model = ReportModel()
        result = model.department_oversee_task_complete_num_sort(date=args['date'])
        return json_response(data=result)


class TaskUnfinishedWarnView(Resource):
    """
    任务未完成预警
    """

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument("department_id", type=int, help='时间', required=False, default=2)
        args = parser.parse_args()
        model = ReportModel()
        result = model.unfinished_task_list(args['department_id'])
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


class WishCompletedView(Resource):
    """
    已完成心愿
    """
    @staticmethod
    def get():
        model = ReportModel()
        result = model.completed_wish_list()
        return json_response(data=result)


class AllWishView(Resource):
    """
    全部心愿列表
    """
    @staticmethod
    def get():
        model = ReportModel()
        result = model.get_wish_list()
        return json_response(data=result)
