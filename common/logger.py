import logging
from settings import BASE_DIR
from pymysql import Error
import traceback
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=BASE_DIR + "/error.log",
                    filemode='a')
logger = logging.getLogger()

# 控制台日志输入
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
ch.setFormatter(formatter)

logger.addHandler(ch)


def error_log(fn):
    """
        处理函数异常，日志记录。
    :param fn:
    :return: 返回None认为函数运行异常
    """
    def log(*args, **kwargs):
        try:
            data = fn(*args, **kwargs)
            return data
        except Error as e:
            s = traceback.format_exc()
            logger.error("%s mysql error %d:%s" % (fn.__name__, e.args[0], e.args[1]))
            logger.error(s)
        except Exception as e:
            logger.error("%s unexpected error %s" % (fn.__name__, str(e)))
            s = traceback.format_exc()
            logger.error(s)
    return log
