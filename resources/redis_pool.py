# -*- coding: utf-8 -*-
# @Time    : 2019/7/25 13:28
# @Author  : 韩朝彪
# @Email   : 1017421922@qq.com
# @File    : mysql_pool.py
# @Software: PyCharm
import redis

from settings import REDIS


class RedisPool(object):
    """
    单例连接池
    """

    __instance = None
    pool = None

    # 连接池实例化一次单例模式
    def __new__(cls, *args, **kwd):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def get_client(self):
        # 连接redis，加上decode_responses=True，写入的键值对中的value为str类型，不加这个参数写入的则为字节类型。
        if self.pool is None:
            self.pool = redis.ConnectionPool(max_connections=3, **REDIS, decode_responses=True)
        redis_client = redis.Redis(connection_pool=self.pool, decode_responses=True)
        return redis_client

    def set_online_status(self, admin):
        """
        设置用户在线状态
        :param admin:
        :return:
        """
        key = "admin_online_{}".format(admin['id'])
        client = self.get_client()
        client.set(key, str(admin), ex=3*60)
        client.close()

    def set_offline_status(self, admin_id):
        """
        设置用户离线状态
        :param admin_id:
        :return:
        """
        key = "admin_online_{}".format(admin_id)
        return self.get_client().delete(key)

    def check_online_status(self, admin_id):
        """
        检查是否在线
        :param admin_id:
        :return:
        """
        key = "admin_online_{}".format(admin_id)
        admin = self.get_client().get(key)
        is_online = True if admin else False
        return is_online

    def get_admin(self, admin_id):
        """
        检查是否在线
        :param admin_id:
        :return:
        """
        key = "admin_online_{}".format(admin_id)
        admin = self.get_client().get(key)
        admin = eval(admin) if admin else None
        return admin


def worker():
    import time
    pool = RedisPool().get_pool()
    time.sleep(1)
    print("id----> %s" % id(pool))


if __name__ == '__main__':
    import threading
    task_list = []
    for one in range(10):
        t = threading.Thread(target=worker)
        task_list.append(t)

    for one in task_list:
        one.start()

    for one in task_list:
        one.join()
