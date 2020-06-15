# -*- coding: utf-8 -*-
# @Time    : 2019/12/6 9:55
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : urls.py
# @Software: PyCharm
from apps import api
from apps.wish.views import EmployeeWishView, AuditWishView, SubmitWishView, EvaluationWishView, DpWishGiveLikeView

api.add_resource(EmployeeWishView, "/wish/release")
api.add_resource(AuditWishView, "/wish/audit")
api.add_resource(SubmitWishView, "/wish/submit")
api.add_resource(EvaluationWishView, "/wish/evaluation")
api.add_resource(DpWishGiveLikeView, '/wish/giveLike')
