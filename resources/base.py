import re
from enum import Enum

from flask import request

import pymysql
from resources.mysql_pool import MysqlPool


class BaseDb(object):

    def __init__(self):
        self.pool = MysqlPool().get_pool()
        self.conn = self.pool.connection()
        self.dict_cur = self.conn.cursor(pymysql.cursors.DictCursor)

    def execute_insert(self, table_name, **kwargs):
        """
        填充sql列占位符
        :param table_name:
        :param kwargs:
        :return:
        """
        sql = "INSERT INTO {}({}) VALUES({})".format(table_name, ','.join(list(kwargs.keys())),
                                                     ','.join(['%s' for _ in range(len(kwargs.keys()))]))
        self.dict_cur.execute(sql, tuple(kwargs.values()))
        return self.dict_cur.lastrowid

    def query_paginate(self, sql, *args, sort=[], page=None, page_size=10):
        """
        查询
        :param sql:
        :param sort: [字段, 'asc']
        :param page:
        :param page_size:
        :return:
        """
        result = re.findall(".*(SELECT|select)(.*)(FROM|from).*", sql)
        count_sql = sql.replace(result[0][1], ' COUNT(*) as number ')

        if sort:
            sql += " ORDER BY {} {} ".format(sort[0], sort[1])
        sql = sql.strip(",")
        if page is not None:
            page = 0 if int(page) < 1 else int(page) - 1
            sql = sql + " LIMIT {}, {}".format(page*int(page_size), page_size)

        if args:
            print(count_sql % args)
            self.dict_cur.execute(count_sql, args)
        else:
            self.dict_cur.execute(count_sql)
        data = self.dict_cur.fetchone()
        count = list(data.values())[0]
        # 列表
        if args:
            self.dict_cur.execute(sql, args)
        else:
            self.dict_cur.execute(sql)
        data = self.dict_cur.fetchall()
        return {"count": count, "pageSize": page_size, "list": data}

    def update_execute(self, table_name, **update_data: dict):
        """
        修改sql数据填充
        :param table_name:
        :param update_data:
        :return:
        """
        update_list = [f'`{key}`="{val}"' for key, val in update_data.items() if key != 'id']
        update = ','.join(update_list)
        sql = "UPDATE {} SET {} WHERE id={}".format(table_name, update, update_data['id'])
        count = self.dict_cur.execute(sql)
        return count

    # def insert_operate_log(self, form, old_value):
    #     """
    #     记录操作日志
    #     :return:
    #     """
    #     # platform = request.user_agent.platform  # 客户端操作系统
    #     # browser = request.user_agent.browser  # 客户端的浏览器
    #     # version = request.user_agent.version  # 客户端浏览器的版本
    #     if 'X-Real-Ip' in request.headers:  # 通过nginx代理后，仍能获取客户端真实ip,需在nginx进行配置
    #         ip = request.headers['X-Real-Ip']
    #     else:
    #         ip = request.remote_addr
    #     admin_id = request.user['id']
    #     primary_id = form.data.get("id") or form.id
    #     sql = "INSERT INTO sys_admin_operate_log(name, table_name, table_id, action_type, operator_id, ip, add_time)" \
    #           " VALUES(%s, %s, %s, %s, %s, %s, NOW())"
    #     self.dict_cur.execute(sql, (form.__name__, form.__table__, primary_id, form.__type__, admin_id, ip))
    #     insert_id = self.dict_cur.lastrowid
    #     field_list = []
    #     if form:
    #         # noinspection PyProtectedMember
    #         for key, val in form._fields.items():
    #             if key == "id":
    #                 continue
    #             elif old_value is None or (key in old_value and form.data[key] != old_value[key]):
    #                 field_list.append([insert_id, key, val.label.text, form.data[key], old_value[key]])
    #     elif old_value:  # 删除操作时，只有原始数据
    #         for key, val in old_value.items():
    #             """"""
    #
    #     sql = "INSERT INTO sys_admin_operate_log_detail(operation_log_id, col_name, col_comment, new_value," \
    #           " old_value) VALUES(%s, %s, %s, %s, %s)"
    #     self.dict_cur.executemany(sql, field_list)

    def __del__(self):
        self.dict_cur.close()
        self.conn.close()
