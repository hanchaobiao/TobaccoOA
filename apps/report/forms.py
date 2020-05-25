# -*- coding: utf-8 -*-
# @Time    : 2019/8/15 17:37
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : forms.py
# @Software: PyCharm
import re
import datetime

from wtforms import Form
from wtforms import StringField, IntegerField, DateTimeField, FieldList, FormField, MultipleFileField
from wtforms.validators import DataRequired, Regexp, Length, AnyOf, Email, ValidationError, NumberRange


class AddWishForm(Form):
    """
    添加心愿
    """
    name = StringField("心愿名称", validators=[DataRequired(message="心愿名称"), Length(max=60)])
    wish_content = StringField("任务介绍", validators=[DataRequired(message="任务介绍不能为空")])


class UpdateWishForm(Form):
    """
    修改心愿
    """
    id = IntegerField("心愿id", validators=[DataRequired("心愿id必填")])
    name = StringField("心愿名称", validators=[DataRequired(message="心愿名称"), Length(max=60)])
    wish_content = StringField("任务介绍", validators=[DataRequired(message="任务介绍不能为空")])
    file_ids = MultipleFileField("文件列表")


class AuditWishForm(Form):
    """
    审核心愿
    """
    id = IntegerField("心愿id", validators=[DataRequired("心愿id必填")])
    status = StringField("心愿名称", validators=[AnyOf(['驳回', '待签收'])])
    department_id = IntegerField("部门id")
    agent_id = IntegerField("经办人id")


class SubmitWishForm(Form):
    """
    提交心愿
    """
    id = IntegerField("心愿id", validators=[DataRequired("心愿id必填")])
    submit_content = StringField("提交内容", validators=[DataRequired("提交内容必填")])


class EvaluationWishForm(Form):
    """
    员工评价
    """
    id = IntegerField("心愿id", validators=[DataRequired("心愿id必填")])
    complain_content = StringField("申诉内容")
    give_like = IntegerField("点赞", validators=[AnyOf([0, 1])])
    send_flower = IntegerField("送花", validators=[AnyOf([0, 1])])
