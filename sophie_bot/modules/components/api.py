from flask import jsonify, request
from sophie_bot import mongodb, flask


@flask.route('/')
def index():
    return "SophieBot API Server!"


@flask.route('/api/is_gbanned/<user_id>')
def is_gbanned(user_id: int):
    print(request.headers)
    gbanned = mongodb.blacklisted_users.find_one({'user': user_id})
    if not gbanned:
        data = {'user_id': user_id, 'gbanned': False}
        return jsonify(data)
    data = mongodb.user_list.find_one({'user_id': user_id})
    if not data:
        data = {}

    data.update(gbanned)
    del data['_id']
    return jsonify(data)
