import time
import datetime
import hashlib

import jwt
import pymysql
from flask import request
from pymysql import escape_string

from resources.base import BaseDb
from resources.redis_pool import RedisPool

from settings import JWT_EXPIRE, SECRET_KEY


class AdminOperateModel(BaseDb):
    """
    管理员模型
    """

    table_name = 'sys_admin'

    def __init__(self):
        BaseDb.__init__(self)
        self.yesterday = datetime.date.today() - datetime.timedelta(1)

    def get_my_memo(self, admin_id, month):
        """
        获取备忘录数据
        :param admin_id:
        :param month:
        :return:
        """
        sql = "SELECT * FROM memo_event WHERE admin_id=%s and DATE_FORMAT(start_date, '%%Y-%%m')=%s"
        self.dict_cur.execute(sql, admin_id, month)
        rows = self.dict_cur.fetchall()
        return rows

    def get_schedule_event(self, user_id, month):
        """
        获取部门行程
        :param user_id:
        :param month:
        :return:
        """
        sql = "SELECT * FROM schedule_event WHERE DATE_FORMAT(start_date, '%%Y-%%m')=%s"
        if user_id:  # 办公室
            sql += " AND operator_id={}".format(user_id)
        self.dict_cur.execute(sql, month)
        rows = self.dict_cur.fetchall()
        user_ids = []
        operator_ids = []
        for row in rows:
            user_ids.append(row['arranged_id'])
            user_ids.append(row['operator_id'])
            operator_ids.append(row['operator_id'])
        if len(rows) == 0:
            return {"query_user": [], "list": []}
        sql = "SELECT * FROM sys_admin WHERE id in %s" % (str(tuple(set(user_ids))).replace(",)", ")"))
        self.dict_cur.execute(sql)
        user_list = self.dict_cur.fetchall()
        user_dict = {user['id']: user['real_name'] for user in user_list}
        for row in rows:
            row['arranged_name'] = user_dict[row['arranged_id']]
            row['operator_name'] = user_dict[row['operator_id']]
        query_list = []
        for operator_id in set(operator_ids):
            query_list.append({"id": operator_id, "name": user_dict[operator_id]})
        return {"query_user": query_list, "list": rows}


if __name__ == "__main__":
    am = AdminOperateModel()
    am.get_schedule_event(None, '2020-05')
