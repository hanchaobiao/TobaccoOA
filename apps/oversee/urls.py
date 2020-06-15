# -*- coding: utf-8 -*-
# @Time    : 2019/12/6 9:55
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : urls.py
# @Software: PyCharm
from apps import api
from apps.oversee.views import ReleaseOverseeTaskView, SubmitOverseeTaskView, AuditOverseeTaskView,\
    OverseeMessageTaskView


api.add_resource(ReleaseOverseeTaskView, "/task/release")
api.add_resource(SubmitOverseeTaskView, "/task/submit")
api.add_resource(AuditOverseeTaskView, "/task/audit")
api.add_resource(OverseeMessageTaskView, "/task/overseeMessage")
