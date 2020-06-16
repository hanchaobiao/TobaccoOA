from settings import API_HOST, API_PORT
from apps import app


if __name__ == '__main__':
    app.run(host=API_HOST, port=API_PORT, debug=False)
