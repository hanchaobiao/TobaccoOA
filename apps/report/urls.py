# -*- coding: utf-8 -*-
# @Time    : 2019/12/6 9:55
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : urls.py
# @Software: PyCharm
from apps import api
from apps.report.views import *

api.add_resource(EmployeeStatusReportView, "/report/employeeStatus")
api.add_resource(LeaderRateView, "/report/leaderRate")
api.add_resource(TaskCompleteSituationView, "/report/taskCompleteSituation")
api.add_resource(TaskTrendView, "/report/taskTrend")
api.add_resource(TaxShowView, "/report/tax")