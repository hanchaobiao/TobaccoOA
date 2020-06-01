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


class AdminModel(BaseDb):
    """
    管理员模型
    """

    table_name = 'sys_admin'

    def __init__(self):
        BaseDb.__init__(self)
        self.yesterday = datetime.date.today() - datetime.timedelta(1)

    def get_admin_by_username(self, username):
        """
        根据用户名查询管理员
        :param username:
        :return:
        """
        sql = "SELECT sys_admin.id, username, password, real_name, position, department_id, " \
              "dict_department.name as department_name, role_id, sys_admin_role.`level` as role_level, role_name, " \
              "is_disable, sys_admin.is_delete, last_login_time " \
              "FROM sys_admin JOIN sys_admin_role ON sys_admin.role_id=sys_admin_role.id " \
              "LEFT JOIN dict_department ON department_id=dict_department.id WHERE username=%s"
        self.dict_cur.execute(sql, username)
        admin = self.dict_cur.fetchone()
        return admin

    def get_admin_by_id(self, admin_id):
        """
        根据用户名查询管理员
        :param admin_id:
        :return:
        """
        sql = "SELECT * FROM sys_admin WHERE id=%s"
        self.dict_cur.execute(sql, admin_id)
        admin = self.dict_cur.fetchone()
        return admin

    def get_admin_by_ids(self, ids):
        """
        获取用户信息
        :param ids:
        :return:
        """
        ids = str(tuple(set(ids))).replace(",)", ")")
        sql = "SELECT id, real_name FROM sys_admin WHERE id in %s" % ids
        self.dict_cur.execute(sql)
        result = self.dict_cur.fetchall()
        return result

    def get_admin_detail(self, admin):
        """
        :param admin:
        :return:
        """
        sql = "SELECT id, name, level FROM dict_department WHERE id=%s"
        self.dict_cur.execute(sql, admin['department_id'])
        department = self.dict_cur.fetchone()

    def is_exists_admin_by_department(self, department_id):
        """
        获取某个部门是否存在员工
        :param department_id:
        :return:
        """
        sql = "SELECT COUNT(*) as num FROM sys_admin WHERE department_id = %s"
        self.dict_cur.execute(sql, department_id)
        return self.dict_cur.fetchone()['num']

    def get_all_role_list(self):
        """
        获取全部角色
        :return:
        """
        self.dict_cur.execute("SELECT * FROM sys_admin_role ")
        rows = self.dict_cur.fetchall()
        return rows

    def login(self, username, password):
        """
        登陆
        :param username:
        :param password:
        :return:
        """
        admin = self.get_admin_by_username(username)
        if admin:
            if admin['is_disable']:
                return {"code": 1, "message": "账户已被禁用"}
            if admin['is_delete']:
                return {"code": 1, "message": "账户已被删除"}
            elif admin['password'] == self.get_md5_password(password):
                login_time = datetime.datetime.now()
                self.update_last_login_time(admin['id'], login_time)
                self.insert_login_log(admin['id'], login_time)
                del admin['last_login_time']
                del admin['password']
                return {"code": 0, "message": "登陆成功", "data": {"admin": admin, "token": self.get_jwt_token(admin)}}
            else:
                return {"code": 1, "message": "密码错误"}
        else:
            return {"code": 1, "message": "账户不存在"}

    def update_last_login_time(self, admin_id, login_time):
        """
        修改上次登陆时间
        :param admin_id:
        :param login_time:
        :return:
        """
        sql = "UPDATE sys_admin SET last_login_time=%s WHERE id=%s".format()
        self.dict_cur.execute(sql, (login_time, admin_id))
        self.conn.commit()

    def insert_login_log(self, admin_id, login_time):
        """
        登陆日志
        :param admin_id:
        :param login_time:
        :return:
        """
        platform = request.user_agent.platform  # 客户端操作系统
        browser = request.user_agent.browser  # 客户端的浏览器
        version = request.user_agent.version  # 客户端浏览器的版本
        if 'X-Real-Ip' in request.headers:  # 通过nginx代理后，仍能获取客户端真实ip,需在nginx进行配置
            ip = request.headers['X-Real-Ip']
        else:
            ip = request.remote_addr
        sql = "INSERT INTO sys_admin_login_log(admin_id, ip, browser, platform, version, add_time) " \
              "values(%s, %s, %s, %s, %s, %s)"
        self.dict_cur.execute(sql, (admin_id, ip, browser, platform, version, login_time))
        self.conn.commit()

    def get_login_log_distinct_admin_list(self):
        """
        获取登陆日志列表
        :return:
        """
        sql = "SELECT id, real_name FROM sys_admin WHERE id IN (SELECT admin_id FROM " \
              " sys_admin_login_log)".format(self.table_name)
        self.dict_cur.execute(sql)
        return self.dict_cur.fetchall()
        return result

    def get_login_log_list(self, admin, name, start_time, end_time, sort_type, page, page_size):
        """
        获取登陆日志列表
        :param admin:
        :param name:
        :param start_time:
        :param end_time:
        :param sort_type:
        :param page:
        :param page_size:
        :return:
        """

        sql = "SELECT sys_admin.real_name, sys_admin.position, log.* FROM sys_admin JOIN sys_admin_login_log as log " \
              "on sys_admin.id=log.admin_id WHERE DATE_FORMAT(log.add_time, '%%Y-%%m-%%d') BETWEEN %s AND %s"
        if name and name.strip():
            sql = sql + " AND real_name like '%%{}%%'".format(escape_string(name.strip()))
        result = self.query_paginate(sql, start_time, end_time, sort=['log.add_time', sort_type],
                                     page=page, page_size=page_size)
        return result

    def get_operate_log_distinct_admin_list(self):
        """
        获取登陆日志列表
        :return:
        """
        sql = "SELECT id, real_name FROM sys_admin WHERE id IN (SELECT operator_id FROM " \
              " sys_admin_operate_log)".format(self.table_name)
        self.dict_cur.execute(sql)
        return self.dict_cur.fetchall()
        return result

    def get_operate_log_list(self, admin, admin_id, operate_type, start_time, end_time, sort_type, page, page_size):
        """
        获取修改日志列表
        :param admin:
        :param admin_id:
        :param operate_type:
        :param start_time:
        :param end_time:
        :param sort_type:
        :param page:
        :param page_size:
        :return:
        """
        sql = "SELECT sys_admin.real_name, log.* FROM sys_admin JOIN sys_admin_operate_log as log " \
              "on sys_admin.id=log.operator_id WHERE DATE_FORMAT(log.add_time, '%%Y-%%m-%%d') BETWEEN %s AND %s"
        if admin_id:
            sql += " AND admin_id={} ".format(admin_id)
        if operate_type:
            sql + " AND operate_type='{}'".format(escape_string(operate_type.strip()))

        result = self.query_paginate(sql, start_time, end_time, sort=['log.add_time', sort_type],
                                     page=page, page_size=page_size)
        return result

    def get_operate_log_detail(self, operate_log_id):
        """
        获取操作日志详情
        :param operate_log_id:
        :return:
        """
        sql = "SELECT * FROM sys_admin_operate_log_detail WHERE operation_log_id=%s"
        self.dict_cur.execute(sql, operate_log_id)
        rows = self.dict_cur.fetchall()
        return rows

    def update_password(self, admin, new_password):
        """
        修改密码
        :param admin:
        :param new_password:
        :return:
        """

        sql = "UPDATE sys_admin SET password=%s WHERE id=%s"
        self.dict_cur.execute(sql, (self.get_md5_password(new_password), admin['id']))

    @staticmethod
    def get_md5_password(password):
        """
        获取md5加密后的密码
        :param password:
        :return:
        """
        md5 = hashlib.md5()
        md5.update(password.encode("utf-8"))
        return md5.hexdigest()

    @staticmethod
    def get_jwt_token(admin):
        """
        生成token
        :param admin:
        :return:
        """
        exp_time = time.time() + JWT_EXPIRE
        token = jwt.encode({'exp': exp_time, **admin},
                           SECRET_KEY, algorithm='HS256')
        return token.decode("utf-8")

    def get_admin_list(self, admin, real_name, department_id, phone, start_date, end_date, page, page_size):
        """
        员工列表
        :param admin:
        :param real_name:
        :param department_id:
        :param phone:
        :param start_date:
        :param end_date:
        :param page:
        :param page_size:
        :return:
        """
        sql = "SELECT sys_admin.id, username, real_name, sex, phone, position, is_disable, last_login_time, status, " \
              "sys_admin.add_time, department_id, dict_department.name as department, dict_department.leader_id, " \
              "dict_department.level, role_id, sys_admin_role.role_name " \
              "FROM sys_admin LEFT JOIN sys_admin_role ON sys_admin.role_id=sys_admin_role.id " \
              "LEFT JOIN dict_department ON sys_admin.department_id=dict_department.id " \
              "WHERE sys_admin.is_delete=0 "
        if real_name:
            sql += " AND real_name like '%{}%' ".format(real_name.strip())
        if department_id:
            sql += " AND (dict_department.id={id} OR path like '{id},%' OR path like '%,{id},%' " \
                   " OR path like '%,{id}')".format(id=department_id)
        if phone:
            sql += " AND phone like '%{}%' ".format(phone)
        if start_date and end_date:
            sql += " AND DATE_FORMAT(add_time, '%%Y-%%m-%%d') BETWEEN '{}' AND '{} ".format(start_date, end_date)
        result = self.query_paginate(sql, page=page, page_size=page_size)
        if len(result['list']) == 0:
            return result

        redis = RedisPool()
        for user in result['list']:
            user['is_online'] = redis.check_online_status(user['id'])
        return result

    def get_admin_by_department_role(self, department_id, role_ids):
        """
        根据部门或权限搜索人员
        :param department_id:
        :param role_ids:
        :return:
        """
        sql = "SELECT sys_admin.id, sys_admin.real_name FROM sys_admin "
        constraints = []
        if role_ids:
            constraints.append(" role_id IN %s" % str(tuple(role_ids)).replace(",)", ")"))
        if department_id:
            constraints.append(f" department_id={department_id}")
        sql = self.append_query_conditions(sql, constraints)
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        return rows

    def add_admin(self, admin):
        """
        添加员工
        :param admin:
        :return:
        """
        try:
            user = self.get_admin_by_username(admin['username'])
            if user:
                return {"code": 1, "message": "用户名已被使用，请重新输入"}
            admin['password'] = self.get_md5_password(admin['password'])
            admin['add_time'] = datetime.datetime.now()
            admin['id'] = self.execute_insert(self.table_name, **admin)
            return {"code": 0, "message": "添加成功"}
        except pymysql.err.IntegrityError:
            return {"code": 1, "message": "该用户名已被使用"}

    def update_admin(self, origin_data, update_data):
        """
        修改员工
        :param origin_data:
        :param update_data:
        :return:
        """
        try:
            if update_data['password']:
                update_data['password'] = self.get_md5_password(update_data['password'])
            else:
                del update_data['password']
            self.execute_update('sys_admin', update_data, origin_data)
            return {"code": 0, "data": update_data}
        except pymysql.err.IntegrityError:
            return {"code": 1, "message": "该用户名已被使用"}

    def delete_admin(self, admin_id):
        """
        删除管理员
        :param admin_id:
        :return:
        """
        sql = "UPDATE sys_admin SET is_delete=1 WHERE id=%s"
        count = self.dict_cur.execute(sql, admin_id)
        return count

    def get_my_message_list(self, admin, msg_type, page, page_size):
        """
        获取个人消息
        :return:
        """
        sql = "SELECT * FROM sys_message WHERE receive_id={} AND receive_time IS NULL".format(admin['id'])
        if msg_type:
            sql += " AND `type`='{}'".format(msg_type)
        result = self.query_paginate(sql, sort=['send_time', 'desc'], page=page, page_size=page_size)
        return result


if __name__ == "__main__":
    am = AdminModel()
    print(am.get_admin_list("张三", "市局机关", 1, 10))
    am.add_admin({"username": "admin1", "password": "123456", "nickname": "测试1", "phone": "17600093237",
                  "role_name": "超级管理员"})
