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

