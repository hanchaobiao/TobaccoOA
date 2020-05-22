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


class AddMemoEventForm(Form):
    """
    添加备忘录
    """
    title = StringField("备忘标题", validators=[DataRequired(message="备忘标题"), Length(max=20)])
    content = StringField("备忘内容", validators=[DataRequired(message="备忘内容不能为空"), Length(max=255)])
    start_date = StringField("开始时间", validators=[DataRequired(message="开始时间不能为空")])
    end_date = StringField("结束时间", validators=[DataRequired(message="结束时间不能为空")])


class UpdateMemoEventForm(Form):
    """
    添加备忘录
    """
    id = IntegerField("备忘id", validators=[DataRequired(message="备忘id不能为空")])
    title = StringField("备忘标题", validators=[DataRequired(message="备忘标题"), Length(max=20)])
    content = StringField("备忘内容", validators=[DataRequired(message="备忘内容不能为空"), Length(max=255)])
    start_date = StringField("开始时间", validators=[DataRequired(message="开始时间不能为空")])
    end_date = StringField("结束时间", validators=[DataRequired(message="结束时间不能为空")])
    is_complete = IntegerField("备忘id", validators=[AnyOf([0, 1])])
