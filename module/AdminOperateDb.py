import time
import datetime
import calendar
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

    def get_my_memo(self, admin_id, date):
        """
        获取备忘录数据
        :param admin_id:
        :param date: 年月
        :return:
        """
        sql = "SELECT id, title, content, admin_id, start_date as start, end_date as end, is_complete, add_time " \
              "FROM memo_event WHERE admin_id=%s and DATE_FORMAT(start_date, '%%Y-%%m')=%s"
        self.dict_cur.execute(sql, (admin_id, date))
        rows = self.dict_cur.fetchall()
        for row in rows:
            row['color'] = 'f1f1f1' if row['is_complete'] else ''
        return rows

    def get_schedule_arranged_list(self, admin):
        """
        获取行程被安排人列表
        :param admin:
        :return:
        """
        sql = "SELECT sys_admin.id, sys_admin.real_name FROM sys_admin " \
              "JOIN sys_admin_role ON role_id=sys_admin_role.id WHERE role_id IN (2, 3) " \
              "AND sys_admin_role.level<=%s OR sys_admin.id=%s"
        self.dict_cur.execute(sql, (admin['role_level'], admin['id']))
        rows = self.dict_cur.fetchall()
        return rows

    def get_schedule_event(self, admin, user_id, date):
        """
        获取部门行程
        :param admin:
        :param user_id:
        :param date:
        :return:
        """
        user_list = self.get_schedule_arranged_list(admin)
        user_dict = {user['id']: user['real_name'] for user in user_list}
        user_ids = [user_id] if user_id else list(user_dict.keys())
        sql = "SELECT schedule_event.id, title, content, arranged_id, operator_id, start_date as `start`, " \
              "end_date as `end`, operator_user.real_name as operator_name FROM schedule_event " \
              "JOIN sys_admin as operator_user ON operator_id=operator_user.id " \
              "WHERE DATE_FORMAT(start_date, '%%Y-%%m')=%s " \
              "AND arranged_id IN {}".format(str(tuple(user_ids)).replace(",)", ")"))
        self.dict_cur.execute(sql, date)
        rows = self.dict_cur.fetchall()
        if len(rows) == 0:
            return {"query_user": user_list, "list": [], "day_total": []}
        for row in rows:
            row['arranged_name'] = user_dict[row['arranged_id']]
        today = datetime.datetime.now()
        _, month_end_day = calendar.monthrange(today.year, today.month)
        start_date = datetime.datetime(today.year, today.month, 1)
        data_list = []
        for i in range(month_end_day):
            date_str = (start_date+datetime.timedelta(i)).strftime('%Y-%m-%d')
            date_dict = {"date": date_str, "people": set(), "event_num": 0}
            for row in rows:
                if str(row['start']) <= date_str <= str(row['end']):
                    date_dict['people'].add(row['arranged_id'])
                    date_dict['event_num'] += 1
            date_dict['people_num'] = len(date_dict['people'])
            date_dict.pop("people")
            if date_dict['people_num'] > 0:
                data_list.append(date_dict)
        return {""
                "query_user": user_list, "list": rows, "day_total": data_list}

    def get_tax_progress(self, year):
        """
        完成税率
        :param year:
        :return:
        """
        sql = "SELECT * FROM tax_progress WHERE year=%s"
        self.dict_cur.execute(sql, year)
        row = self.dict_cur.fetchone()
        sql = "SELECT distinct year FROM tax_progress order by year"
        self.dict_cur.execute(sql)
        years = self.dict_cur.fetchall()
        return {"tax": row, "years": years}

    def replace_tax_progress(self, data):
        """
        完成税率
        :param data:
        :return:
        """
        sql = "REPLACE INTO tax_progress(`year`, complete_tax_money, total_tax_money, modify_time)" \
              " VALUES(%s, %s, %s, now())"
        count = self.dict_cur.execute(sql, (data['year'], data['complete_tax_money'], data['total_tax_money']))
        return count


if __name__ == "__main__":
    am = AdminOperateModel()
    print(am.get_schedule_event({"id": 2, "role_level": 9}, None, '2020-05'))
