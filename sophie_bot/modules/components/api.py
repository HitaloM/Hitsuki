import threading
import ujson

from flask import Flask
from sophie_bot import mongodb

app = Flask(__name__)


@app.route('/')
def index():
    return "SophieBot API Server!"


@app.route('/api/is_gbanned/<user_id>')
def is_gbanned(user_id):
    gbanned = mongodb.blacklisted_users.find_one({'user': user_id})
    if not gbanned:
        data = {'user_id': user_id, 'gbanned': False}
        return ujson.dumps(data)


def start(i):
    app.run(debug=True, use_reloader=False)


i = None
t = threading.Thread(target=start, args=(i,))
t.start()
