# -*- coding: utf-8 -*-
from flask import abort, escape, Flask, request
from flask import render_template, send_from_directory

from datetime import datetime

from cache_bust import create_hash
from messages import MessageParser
from models import Chat, Users
from config import GUEST_NAME

app = Flask(__name__, static_folder='static', static_url_path='')


@app.route('/robots.txt')
@app.route('/style.css')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route("/<user_id>", methods=['GET'])
def chat_read(user_id):
    user = authenticate(user_id)
    timestamp = int(datetime.now().timestamp())

    with Chat() as chat:
        messages = chat.read(150)
    
    latest_pk = messages[-1].pk if messages else 0

    return render_template('alfachat.html',
                           user=user,
                           timestamp=timestamp,
                           messages=messages,
                           guest=GUEST_NAME,
                           users=Users().all(),
                           latest_pk=latest_pk)


@app.route("/<user_id>", methods=['POST'])
def chat_write(user_id):
    user = authenticate(user_id)

    raw_text = escape(request.form['message'])

    with Chat() as chat:
        chat.write(MessageParser().parse(user, raw_text))

    return chat_read(user_id)


@app.route("/archiv/<user_id>")
def archive(user_id):
    user = authenticate(user_id)

    with Chat() as chat:
        messages = chat.read()

    return render_template('archive.html', messages=messages, user=user)


@app.route("/latest/<user_id>/<latest_pk>")
def latest(user_id, latest_pk):
    user = authenticate(user_id)

    with Chat() as chat:
        messages = list(filter(lambda m: m.is_visible_to(
            user), chat.read_latest(latest_pk)))

    return "[{0}]".format(",".join([m.to_json() for m in messages]))


def authenticate(user_id):
    return Users().find_by_user_id(user_id) or abort(404)


@app.url_defaults
def hashed_url_for_static_file(endpoint, values):
    create_hash(endpoint, values, app)
