import wtforms_json

from settings import API_HOST, API_PORT
from apps import app

wtforms_json.init()  # 解决json数据传入wtforms表单，取值问题，正常传入类型需要是{'name': ['han']}，因此使用此插件处理


if __name__ == '__main__':
    app.run(host=API_HOST, port=API_PORT, debug=False)
