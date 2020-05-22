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
        sql = "SELECT * FROM memo_event WHERE admin_id=%s and DATE_FORMAT('%Y-%m')=%s"
        self.dict_cur.execute(sql, admin_id, month)
        rows = self.dict_cur.fetchall()
        return rows


if __name__ == "__main__":
    am = AdminModel()
    print(am.get_admin_list("张三", "市局机关", 1, 10))
    am.add_admin({"username": "admin1", "password": "123456", "nickname": "测试1", "phone": "17600093237",
                  "role_name": "超级管理员"})
