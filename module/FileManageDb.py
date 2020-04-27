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


class FileManageModel(BaseDb):
    """
    文件管理
    """

    table_name = "sys_file_manage"

    def __init__(self):
        BaseDb.__init__(self)
        self.yesterday = datetime.date.today() - datetime.timedelta(1)

    def get_file_by_id(self, file_id):
        """
        获取文件
        :param file_id:
        :return:
        """
        sql = "SELECT * FROM {} WHERE id=%s".format(self.table_name)
        self.dict_cur.execute(sql, file_id)
        return self.dict_cur.fetchone()

    def get_distinct_admin_list(self):
        """
        获取文件
        :return:
        """
        sql = "SELECT id, real_name FROM sys_admin WHERE id IN (SELECT admin_id FROM {})".format(self.table_name)
        self.dict_cur.execute(sql)
        return self.dict_cur.fetchall()

    def get_file_list(self, file_name, file_format, admin_id, start_date, end_date, page, page_size):
        """
        获取文件列表
        :param file_name:
        :param file_format:
        :param admin_id:
        :param start_date:
        :param end_date:
        :param page:
        :param page_size:
        :return:
        """
        sql = """
            SELECT file.*, sys_admin.real_name FROM sys_file_manage as file 
            JOIN sys_admin ON file.admin_id=sys_admin.id
            WHERE file.is_delete!=1
        """
        if file_name:
            sql += " AND file_name like '%{}%' ".format(escape_string(file_name.strip()))
        if file_format:
            sql += " file_format = '{}' ".format(escape_string(file_format))
        if admin_id:
            sql += " AND admin_id={} ".format(admin_id)
        if start_date and end_date:
            sql += " AND DATE_FORMAT(file.add_time, '%%Y-%%m-%%d') BETWEEN '{}' AND '{} ".format(start_date, end_date)
        result = self.query_paginate(sql, page=page, page_size=page_size)
        for res in result['list']:
            if res['size']/1024 < 1024:
                res['size'] = str(round(res['size']/1024, 2))+'KB'
            else:
                res['size'] = str(round(res['size']/1024/1024, 2)) + 'MB'
        return result

    def insert_file_info(self, file_info):
        """
        添加文件信息
        :param file_info:
        :return:
        """
        file_info['id'] = self.execute_insert(self.table_name, **file_info)
        return file_info


if __name__ == "__main__":
    am = FileManageModel()
