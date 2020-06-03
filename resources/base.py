import re

from flask import request

import pymysql
from resources.mysql_pool import MysqlPool
from settings import MYSQL


class BaseDb(object):

    def __init__(self):
        self.pool = MysqlPool().get_pool()
        self.conn = self.pool.connection()
        self.dict_cur = self.conn.cursor(pymysql.cursors.DictCursor)

    def query_column_comment(self, table_name):
        """
        查询列注释
        :param table_name:
        :return:
        """
        sql = "SELECT column_name, column_comment FROM INFORMATION_SCHEMA.Columns " \
              "where table_name=%s and table_schema=%s"
        self.dict_cur.execute(sql, (table_name, MYSQL['db']))
        rows = self.dict_cur.fetchall()
        column_dict = {row['COLUMN_NAME']: row['COLUMN_COMMENT'] for row in rows}
        return column_dict

    def insert_operate_log(self, table_name, table_id, method, action_desc):
        """
        插入基础日志
        :param table_name:
        :param table_id:
        :param method:
        :param action_desc:
        :return:
        """
        if 'X-Real-Ip' in request.headers:  # 通过nginx代理后，仍能获取客户端真实ip,需在nginx进行配置
            ip = request.headers['X-Real-Ip']
        else:
            ip = request.remote_addr
        admin_id = request.user['id']
        sql = "INSERT INTO sys_admin_operate_log(name, table_name, table_id, operate_type, operator_id, ip, add_time)" \
              " VALUES(%s, %s, %s, %s, %s, %s, NOW())"
        self.dict_cur.execute(sql, (action_desc, table_name, table_id, method, admin_id, ip))
        insert_id = self.dict_cur.lastrowid
        return insert_id

    def insert_operate_detail_log(self, field_list):
        """
        插入具体字段日志
        :param field_list:
        :return:
        """
        sql = "INSERT INTO sys_admin_operate_log_detail(operation_log_id, col_name, col_comment, new_value," \
              " old_value) VALUES(%s, %s, %s, %s, %s)"
        self.dict_cur.executemany(sql, field_list)

    def insert_log(self, table_name, table_id, desc, insert_data=None, extra_fields=[]):
        """
        新增操作日志记录
        :param table_name:
        :param table_id:
        :param desc:
        :param insert_data:
        :param extra_fields: [{"name": "", "value": "", "desc": ""}]
        :return:
        """
        table_comment = self.query_column_comment(table_name)
        if insert_data is None:
            sql = f"SELECT * FROM {table_name} WHERE id=%s"
            self.dict_cur.execute(sql, table_id)
            insert_data = self.dict_cur.fetchone()
        insert_id = self.insert_operate_log(table_name, table_id, '新增', desc)
        field_list = []
        for key, val in insert_data.items():
            if table_comment.get(key):
                field_list.append([insert_id, key, table_comment[key], val, None])
        for item in extra_fields:
            field_list.append([insert_id, item['name'], item['desc'], item['value'], None])
        self.insert_operate_detail_log(field_list)

    def update_log(self, table_name, table_id, desc, origin_data, new_data=None):
        """
        修改操作日志记录
        :param table_name:
        :param table_id:
        :param desc:
        :param origin_data:
        :param new_data:
        :return:
        """
        table_comment = self.query_column_comment(table_name)
        if new_data is None:
            sql = f"SELECT * FROM {table_name} WHERE id=%s"
            self.dict_cur.execute(sql, table_id)
            new_data = self.dict_cur.fetchone()
        insert_id = self.insert_operate_log(table_name, table_id, '修改', desc)
        field_list = []
        for key, val in origin_data.items():
            if table_comment.get(key) and key in new_data and val != new_data[key]:
                field_list.append([insert_id, key, table_comment[key], new_data[key], val])
        self.insert_operate_detail_log(field_list)

    def delete_log(self, table_name, table_id, desc, delete_data=None):
        """
        删除操作日志记录
        :param table_name:
        :param table_id:
        :param desc:
        :param delete_data:
        :return:
        """
        table_comment = self.query_column_comment(table_name)
        if delete_data is None:
            sql = f"SELECT * FROM {table_name} WHERE id=%s"
            self.dict_cur.execute(sql, table_id)
            delete_data = self.dict_cur.fetchone()
        insert_id = self.insert_operate_log(table_name, table_id, '删除', desc)
        field_list = []
        for key, val in delete_data.items():
            if table_comment.get(key):
                field_list.append([insert_id, key, table_comment[key], None, val])
        self.insert_operate_detail_log(field_list)

    def set_autocommit(self, flag):
        self.dict_cur.execute("set autocommit = {}".format(flag))

    def start_transaction(self):
        """
        开启事务,set autocommit=0指事务非自动提交，自此句执行以后，每个SQL语句或者语句块所在的事务都需要显示"commit"才能提交事务。
        1、不管autocommit 是1还是0
        START TRANSACTION 后，只有当commit数据才会生效，ROLLBACK后就会回滚。
        2、当autocommit 为 0 时
        不管有没有START TRANSACTION。
        只有当commit数据才会生效，ROLLBACK后就会回滚。
        3、如果autocommit 为1 ，并且没有START TRANSACTION 。
        调用ROLLBACK是没有用的。即便设置了SAVEPOINT。
        :return:
        """
        self.dict_cur.execute("start transaction")

    @staticmethod
    def append_query_conditions(sql, conditions):
        if len(conditions) == 0:
            return sql
        elif sql.strip().endswith('where') or sql.strip().endswith('WHERE'):
            sql = sql + ' AND '.join(conditions)
        else:
            sql = sql + " WHERE " + ' AND '.join(conditions)
        return sql

    def get_data_by_id(self, table_name, table_id):
        """
        获取任务信息
        :param table_name:
         :param table_id:
        :return:
        """
        sql = "SELECT * FROM {} WHERE id={}".format(table_name, table_id)
        self.dict_cur.execute(sql)
        return self.dict_cur.fetchone()

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

    def execute_insert_many(self, table_name, data_list):
        """
        填充sql列占位符
        :param table_name:
        :param data_list:
        :return:
        """
        if len(data_list) == 0:
            return None
        kwargs = data_list[0]
        value_list = [tuple(item.values()) for item in data_list]
        sql = "INSERT INTO {}({}) VALUES({})".format(table_name, ','.join(list(kwargs.keys())),
                                                     ','.join(['%s' for _ in range(len(kwargs.keys()))]))
        self.dict_cur.executemany(sql, value_list)
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
        result = re.findall(".*(SELECT|select)(.*)(FROM|from).*", sql, re.S)
        count_sql = sql.replace(result[0][1], ' COUNT(*) as number ')

        if sort:
            sql += " ORDER BY {} {} ".format(sort[0], sort[1])
        sql = sql.strip(",")
        if page is not None:
            page = 0 if int(page) < 1 else int(page) - 1
            sql = sql + " LIMIT {}, {}".format(page*int(page_size), page_size)
        print(sql)
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

    def execute_update(self, table_name, update_data: dict, origin_data=None, default_data={}, extra_conditions=[]):
        """
        修改sql数据填充
        :param table_name:
        :param origin_data:
        :param update_data:
        :param default_data: 一些需要动态设置的值，但是不进行是否修改的数据比较，比如now()
        :param extra_conditions:
        :return:
        """
        diff = False  # 比较数据是否不同
        if origin_data is None:
            diff = True
        else:
            for key, val in update_data.items():
                if val != origin_data.get(key):
                    diff = True
                    break
            if default_data:
                update_data.update(default_data)
        if diff is False:
            return 0
        update_list = [f'`{key}`="{val}"' for key, val in update_data.items() if key != 'id']
        update = ','.join(update_list)
        sql = "UPDATE {} SET {} WHERE id={}".format(table_name, update, update_data['id'])
        if len(extra_conditions) > 0:
            sql += " AND " + " AND ".join(extra_conditions)
        print(sql)
        count = self.dict_cur.execute(sql)
        return count

    def execute_delete(self, table_name, conditions=[]):
        """
        删除
        :param table_name:
        :param conditions:
        :return:
        """
        sql = f"DELETE FROM {table_name} "
        if len(conditions) > 0:
            sql += " WHERE " + " AND ".join(conditions)
        count = self.dict_cur.execute(sql)
        return count

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
