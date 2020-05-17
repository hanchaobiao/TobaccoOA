import functools
from resources.base import BaseDb


def db_transaction(method):
    """
    事务
    :param method:
    :return:
    """
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        db = BaseDb()
        try:
            db.set_autocommit(0)
            result = method(*args, **kwargs)
            db.conn.commit()
            db.set_autocommit(1)
            return result
        except Exception as e:
            print(e)
            db.conn.rollback()
            raise e
    return wrapper
