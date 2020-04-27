# -*- coding:utf-8 -*-
import threading
from DBUtils.PooledDB import PooledDB
import pymysql
from settings import MYSQL


class MysqlPool(object):
    """
    单例连接池
    """

    _instance_lock = threading.Lock()
    __instance = None
    pool = None

    # 连接池实例化一次单例模式
    def __new__(cls, *args, **kwd):
        if MysqlPool.__instance is None:
            with cls._instance_lock:
                MysqlPool.__instance = object.__new__(cls)
                cls.pool = MysqlPool.__instance.get_pool()
        return MysqlPool.__instance

    def get_pool(self):
        if self.pool is None:
            self.pool = PooledDB(
                creator=pymysql,  # 使用链接数据库的模块
                mincached=2,  # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
                maxcached=6,  # 链接池中最多闲置的链接，0和None不限制
                maxshared=3,
                # 链接池中最多共享的链接数量，0和None表示全部共享。PS: 无用，因为pymysql和MySQLdb等模块的 threadsafety都为1，
                # 所有值无论设置为多少，_maxcached永远为0，所以永远是所有链接都共享。
                maxconnections=30,  # 连接池允许的最大连接数，0和None表示不限制连接数
                blocking=True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
                maxusage=None,  # 一个链接最多被重复使用的次数，None表示无限制
                setsession=None,  # 开始会话前执行的命令列表。如：["set datestyle to ...", "set time zone ..."]
                # ping MySQL服务端，检查是否服务可用。# 如：0 = None = never, 1 = default = whenever it is requested,
                # 2 = when a cursor is created, 4 = when a query is executed, 7 = always
                **MYSQL,
                # use_unicode=False,
                autocommit=True
            )
        return self.pool

    def __del__(self):
        self.pool.close()


def worker():
    import time
    pool = MysqlPool()
    # pool = pool.get_sc_pool()
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











