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
api.add_resource(DownloadFileView, "/download")
api.add_resource(MemoEventView, "/memoEvent")
api.add_resource(ScheduleView, "/scheduleEvent")
api.add_resource(DepartmentNoticeView, "/departmentNotice")
api.add_resource(TaxProgressView, "/taxProgress")
api.add_resource(EmployeeStatusView, "/employeeStatus")