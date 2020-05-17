# -*- coding: utf-8 -*-
# @Time    : 2019/12/6 9:55
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : urls.py
# @Software: PyCharm
from apps import api
from apps.admin_operation.views import *


api.add_resource(UseAdminView, "/useAdmin")
api.add_resource(AdminSelectView, "/admin/select")
api.add_resource(DepartmentView, "/department")
api.add_resource(FileManageView, "/fileManage")