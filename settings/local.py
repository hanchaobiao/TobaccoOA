import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 生产环境数据查询服务配置
API_HOST = "0.0.0.0"
API_PORT = 5001
API_DEBUG = False    # 调试模式，即修改代码后立马响应，无需重启服务，但是不能用于生产环境


MYSQL = {
    "db": "tobacco_office",
    "host": "47.99.51.135",
    "port": 3306,
    "user": "root",
    "passwd": "hbuasxyl_2019",
}


REDIS = {
        "host": "47.105.138.133",
        "port": "6379",
        "db": 1,
        "password": "bjmrkj_2019"
}


# Token 有效期
JWT_EXPIRE = 7*7*3600

ACTIVE_EXPIRE = 30*60*60


SECRET_KEY = "7e41I1kCRN5Y*pw13Mc4%rPL0FSj%^tA"  # 使用session 必须加上


MEDIA_PREFIX = "http://127.0.0.1:5001/local_media"
