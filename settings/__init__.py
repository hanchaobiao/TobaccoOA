import os
# 通过环境变量DEPLOY判断读取的配置文件
# linux 下 在个人目录中的 .bash_profile设置环境变量
# report DEPLOY=prod
# os.environ.setdefault('DEPLOY', 'prod')
deploy = os.environ.get("DEPLOY") or "dev"
print('此时的环境变量', deploy)
if deploy == 'dev':
    from settings.local import *
elif deploy == 'prod':
    from settings.prod import *  # todo 暂时 测试环境
else:
    from settings.local import *
