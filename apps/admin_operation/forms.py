# -*- coding: utf-8 -*-
# @Time    : 2019/8/15 17:37
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : forms.py
# @Software: PyCharm
import re
import datetime

from wtforms import Form
from wtforms import StringField, IntegerField, DecimalField
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


class AddScheduleEventForm(Form):
    """
    添加行程
    """
    arranged_id = IntegerField("被安排人", validators=[DataRequired(message="被安排人不能为空")])
    title = StringField("行程标题", validators=[DataRequired(message="行程标题不能为空"), Length(max=30)])
    content = StringField("行程内容", validators=[DataRequired(message="行程内容不能为空"), Length(max=255)])
    start_date = StringField("开始时间", validators=[DataRequired(message="开始时间不能为空")])
    end_date = StringField("结束时间", validators=[DataRequired(message="结束时间不能为空")])


class UpdateScheduleEventForm(Form):
    """
    修改行程
    """
    id = IntegerField("备忘id", validators=[DataRequired(message="备忘id不能为空")])
    arranged_id = IntegerField("被安排人", validators=[DataRequired(message="被安排人不能为空")])
    title = StringField("行程标题", validators=[DataRequired(message="行程标题不能为空"), Length(max=30)])
    content = StringField("行程内容", validators=[DataRequired(message="行程内容不能为空"), Length(max=255)])
    start_date = StringField("开始时间", validators=[DataRequired(message="开始时间不能为空")])
    end_date = StringField("结束时间", validators=[DataRequired(message="结束时间不能为空")])


class UpdateTaxProgressForm(Form):
    """
    税率
    """
    complete_tax_money = DecimalField("完成税额",  places=10, rounding=2)
    total_tax_money = DecimalField("模板税额", places=10, rounding=2)
    year = IntegerField("年份", validators=[NumberRange(min=1900, max=2100)])


class AddDepartmentNoticeForm(Form):
    """
    发布公告
    """
    title = StringField("公告标题",  validators=[DataRequired(message="公告标题必填"), Length(max=30)])
    content = StringField("公告内容", validators=[DataRequired(message="公告内容必填"), Length(max=255)])


class UpdateDepartmentNoticeForm(Form):
    """
    发布公告
    """
    id = IntegerField("公告id", validators=[DataRequired(message="公告id不能为空")])
    title = StringField("公告标题",  validators=[DataRequired(message="公告标题必填"), Length(max=30)])
    content = StringField("公告内容", validators=[DataRequired(message="公告内容必填"), Length(max=255)])
