from pymysql.cursors import DictCursor
from flask import request

from settings import MYSQL
from resources.mysql_pool import MysqlPool


class AdminOperateLog(object):
    """
    用户操作日志记录
    """

    def __init__(self):
        self.pool = MysqlPool().get_pool()
        self.conn = self.pool.connection()
        self.dict_cur = self.conn.cursor(DictCursor)

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
