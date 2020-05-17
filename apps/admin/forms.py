# -*- coding: utf-8 -*-
# @Time    : 2019/8/15 17:37
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : forms.py
# @Software: PyCharm
import re

from wtforms import Form
from wtforms import StringField, IntegerField, FileField, MultipleFileField
from wtforms.validators import DataRequired, Regexp, Length, AnyOf, Email, ValidationError, NumberRange


MOBILE_REGEX = r"^1[358]\d{9}$|^1[48]7\d{8}$|^176\d{8}$"


class LoginForm(Form):
    """
    短信验证码
    """
    account = StringField("账号", validators=[DataRequired(message="账号不能为空"), Length(min=1, max=16)])
    password = StringField("密码", validators=[DataRequired(message="密码不能为空"), Length(min=1, max=16)])


class AddAdminForm(Form):
    """
    添加管理员
    """
    username = StringField("用户名", validators=[DataRequired(message="用户名必须为5-16字符长度"), Length(min=5, max=16)])
    password = StringField("密码", validators=[DataRequired(message="密码必须为5-16字符长度"), Length(min=5, max=16)])
    real_name = StringField("姓名", validators=[DataRequired(message="姓名必填"), Length(min=1, max=10)])
    sex = StringField("性别", validators=[AnyOf(['男', '女'])])
    position = StringField("职务", validators=[DataRequired(message="职务必填")])
    department_id = IntegerField("所属部门", validators=[DataRequired(message="部门必填")])
    is_disable = IntegerField("是否禁用", validators=[AnyOf([0, 1])])
    phone = StringField("手机号码", validators=[DataRequired(message="请输入手机号码"),
                        Regexp(MOBILE_REGEX, message="请输入合法的手机号码")])
    role_ids = MultipleFileField("角色", validators=[DataRequired("请选择角色")])


class UpdateAdminForm(Form):
    """
    修改管理员
    """
    id = IntegerField("管理员id", validators=[DataRequired(message="id不能为空")])
    password = StringField("密码")
    real_name = StringField("姓名", validators=[DataRequired(message="姓名必填"), Length(min=1, max=10)])
    sex = StringField("性别", validators=[AnyOf(['男', '女'])])
    position = StringField("职务", validators=[DataRequired(message="职务必填")])
    department_id = IntegerField("所属部门", validators=[DataRequired(message="部门必填")])
    is_disable = IntegerField("是否禁用", validators=[AnyOf([0, 1])])
    phone = StringField("手机号码", validators=[DataRequired(message="请输入手机号码"),
                                            Regexp(MOBILE_REGEX, message="请输入合法的手机号码")])
    role_ids = MultipleFileField("角色", validators=[DataRequired("请选择角色")])

    # noinspection PyMethodMayBeStatic
    def validate_password(self, field):
        if field.data and 5 <= len(field.data) <= 15 is False:
            raise ValueError("密码长度在5-15字符")


class UpdatePasswordForm(Form):
    """
    修改密码
    """

    __table__ = 'sys_admin'
    __name__ = '修改个人密码'
    __type__ = '修改'

    old_password = StringField("当前密码", validators=[DataRequired(message="密码必须为5-16字符长度"), Length(min=5, max=16)])
    password = StringField("密码", validators=[DataRequired(message="密码必须为5-16字符长度"), Length(min=5, max=16)])
    confirm_password = StringField("确认密码", validators=[DataRequired(message="密码必须为5-16字符长度"), Length(min=5, max=16)])

