# -*- coding: utf-8 -*-
# @Time    : 2019/5/5 18:08
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : task.py
# @Software: 异步任务
from module.OverseeTaskDb import OverseeTaskModel


def send_sys_message(message_list):
    """
    发送督办信息
    :param message_list:
    :return:
    """
    model = OverseeTaskModel()
    model.execute_insert_many('sys_message', message_list)
    for item in message_list:
        user = model.get_data_by_id('sys_admin', item['receive_id'])
        print(user['phone'])
