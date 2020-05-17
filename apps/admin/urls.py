# -*- coding: utf-8 -*-
# @Time    : 2019/12/6 9:55
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : urls.py
# @Software: PyCharm
from apps import api
from apps.admin.views import *


api.add_resource(LoginView, "/login")
api.add_resource(AdminManageView, "/admin/manage")
api.add_resource(AdminLoginLogView, "/admin/loginLog")
api.add_resource(AdminOperateLogView, "/admin/operateLog")
api.add_resource(UpdatePasswordView, "/admin/updatePassword")
api.add_resource(AdminRoleView, "/admin/role")