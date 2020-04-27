# -*- coding: utf-8 -*-
# @Time    : 2019/8/15 17:37
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : forms.py
# @Software: PyCharm
import re
import datetime

from wtforms import Form
from wtforms import StringField, IntegerField, MultipleFileField
from wtforms.validators import DataRequired, Regexp, Length, AnyOf, Email, ValidationError, NumberRange


class AddDepartmentForm(Form):
    """
    添加部门
    """

    name = StringField("部门名称", validators=[DataRequired(message="部门名称不能为空")])
    pid = IntegerField("上级部门", validators=[DataRequired(message="部门名称不能为空")])
    leader_id = StringField("负责人")


class UpdateDepartmentForm(Form):
    """
    修改部门
    """

    id = IntegerField("部门id", validators=[DataRequired(message="部门id不能为空")])
    name = StringField("部门名称", validators=[DataRequired(message="部门名称不能为空")])
    leader_id = StringField("负责人")

