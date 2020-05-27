import os
import datetime

from urllib import parse

from resources.base import BaseDb
from settings import MEDIA_PREFIX


class WishModel(BaseDb):
    """
    心愿
    """

    def __init__(self):
        BaseDb.__init__(self)
        self.yesterday = datetime.date.today() - datetime.timedelta(1)
        self.departments = []

    def get_employee_wish_detail(self, admin, wish_id):
        """
        心愿详情
        :param admin:
        :param wish_id:
        :return:
        """
        wish = {'employee_file': [], 'submit_file': []}
        sql = "SELECT * FROM employee_wish_file WHERE wish_id=%s"
        self.dict_cur.execute(sql, wish_id)
        file_list = self.dict_cur.fetchall()
        for item in file_list:
            item['url'] = parse.urljoin(MEDIA_PREFIX, item['file_path'])
            if item['file_type'] == 1:
                wish['employee_file'].append(item)
            else:
                wish['submit_file'].append(item)

        return wish

    def get_employee_wish_list(self, admin, name, status, page, page_size):
        """
        心愿列表
        :param admin:
        :param name:
        :param status:
        :param page:
        :param page_size:
        :return:
        """
        sql = """
        SELECT employee_wish.*, employee.real_name as employee_name, agent.real_name as agent_name, 
        dict_department.name as department_name
        FROM employee_wish JOIN sys_admin as employee ON employee_id=employee.id 
        LEFT JOIN sys_admin as agent ON agent_id=agent.id 
        LEFT JOIN dict_department ON employee_wish.department_id = dict_department.id
        """
        conditions = []
        if admin['role_id'] not in [1, 2, 3]:
            conditions.append( "(employee_wish.agent_id={admin_id} OR employee_wish.employee_id={admin_id})".
                               format(admin['id']))
        if name:
            conditions.append("employee_wish.name like '%{}%'".format(name))
        if status:
            conditions.append("status.status='{}'".format(status))
        result = self.query_paginate(sql, sort=['employee_wish.add_time', 'desc'], page=page, page_size=page_size)
        return result

    def reset_wish_file(self, task_id, file_ids):
        """
        重置任务文件
        :param task_id:
        :param file_ids:
        :return:
        """
        sql = "DELETE FROM rel_task_file WHERE task_id={}".format(task_id)
        if len(file_ids):
            sql += " AND file_id NOT IN %s" % (str(tuple(file_ids)).replace(",)", ")"))
        self.dict_cur.execute(sql)
        if len(file_ids):
            sql = f"INSERT IGNORE INTO rel_task_file(task_id, file_id) VALUES({task_id}, %s)"
            self.dict_cur.executemany(sql, file_ids)


if __name__ == "__main__":
    am = WishModel()
