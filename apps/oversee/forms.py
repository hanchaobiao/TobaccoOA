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


class AddOverseeDetailTaskForm(Form):
    """
    修改部门
    """

    agent_id = IntegerField("经办人", validators=[DataRequired(message="经办人不能为空")])
    department_id = IntegerField("部门id", validators=[DataRequired(message="部门id")])
    start_time = StringField("开始时间", validators=[DataRequired(message="开始时间不能为空")])
    end_time = StringField("结束时间", validators=[DataRequired(message="结束时间不能为空")])
    coordinator_ids = MultipleFileField(label="协办人", default=[])


class AddOverseeTaskForm(Form):
    """
    添加督办任务
    """
    # task_no = StringField("任务编号", validators=[DataRequired(message="任务名称不能为空"), Length(max=50)])
    type = StringField("任务类型", validators=[AnyOf(['重大事务', '紧急事务', '专项事务', '常规事务'])])
    name = StringField("任务名称", validators=[DataRequired(message="任务名称不能为空"), Length(max=60)])
    file_ids = MultipleFileField(label="涉及文件")
    introduce = StringField("任务介绍", validators=[DataRequired(message="任务介绍不能为空")])
    oversee_id = IntegerField("督办人", validators=[DataRequired(message="督办人不能为空")])
    oversee_details = FieldList(FormField(AddOverseeDetailTaskForm), validators=[DataRequired(message="子任务不能为空")])


class UpdateOverseeDetailTaskForm(Form):
    """
    修改督办任务子任务
    """
    id = IntegerField("子任务id", validators=[DataRequired("子任务id必填")])
    agent_id = IntegerField("经办人", validators=[DataRequired(message="经办人不能为空")])
    department_id = IntegerField("部门id", validators=[DataRequired(message="部门id")])
    start_time = DateTimeField("开始时间", validators=[DataRequired(message="开始时间不能为空")])
    end_time = DateTimeField("结束时间", validators=[DataRequired(message="结束时间不能为空")])
    coordinator_ids = MultipleFileField(label="协办人", default=[])


class UpdateOverseeTaskForm(Form):
    """
    修改督办任务
    """
    id = IntegerField("任务id", validators=[DataRequired("任务id必填")])
    type = StringField("任务类型", validators=[AnyOf(['重大事务', '紧急事务', '专项事务', '常规事务'])])
    # task_no = StringField("任务编号", validators=[DataRequired(message="任务名称不能为空"), Length(max=50)])
    name = StringField("任务名称", validators=[DataRequired(message="任务名称不能为空"), Length(max=60)])
    file_ids = MultipleFileField(label="涉及文件")
    introduce = StringField("任务介绍", validators=[DataRequired(message="任务介绍不能为空")])
    oversee_id = IntegerField("督办人", validators=[DataRequired(message="督办人不能为空")])
    oversee_details = FieldList(FormField(UpdateOverseeDetailTaskForm), validators=[DataRequired(message="子任务不能为空")])


class SubmitOverseeTaskForm(Form):
    """
    提交任务
    """
    id = IntegerField("任务id", validators=[DataRequired("任务id必填")])
    file_ids = MultipleFileField("删除文件id")
    submit_remark = StringField("提交备注", validators=[DataRequired(message="提交备注不能为空")])


class AuditOverseeTaskForm(Form):
    """
    审批任务
    """
    id = IntegerField("子任务id", validators=[DataRequired("子任务id必填")])
    status = StringField("审核状态", validators=[AnyOf(['任务完成', '审核驳回'])])
    audit_remark = StringField("审核意见", validators=[DataRequired(message="审核意见不能为空")])


class OverseeMessageForm(Form):
    """
    给经办人发送提示消息
    """
    content = StringField("留言", validators=[DataRequired("留言")])
    task_detail_id = IntegerField("子任务id", validators=[DataRequired("子任务id必填")])

