import socket


def get_host_ip():
    """
    查询本机ip地址
    :return:
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


ip_addr = get_host_ip()

if ip_addr != '172.16.83.219':
    print('测试环境')
    from settings.local import *
    MEDIA_PREFIX = "http://{}:8010/media".format(ip_addr)
else:
    print('生产环境')
    from settings.prod import *  # todo 暂时 测试环境


