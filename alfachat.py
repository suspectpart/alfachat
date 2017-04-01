# -*- coding: utf-8 -*-
from flask import abort, escape, Flask, request
from flask import render_template
from flask import send_from_directory
from cache_bust import create_hash
from messages import MessageParser
from models import Chat, User

app = Flask(__name__, static_folder='static', static_url_path='')


@app.route('/robots.txt')
@app.route('/style.css')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route("/<user_id>", methods=['GET'])
def chat_read(user_id):
    return render_template('alfachat.html', user=authenticate(user_id))


@app.route("/<user_id>", methods=['POST'])
def chat_write(user_id):
    user = authenticate(user_id)

    raw_text = escape(request.form['message'])

    with Chat() as chat:
        chat.write(MessageParser().parse(user, raw_text))

    return render_template('alfachat.html', user=user)


@app.route("/messages/<user_id>")
def messages(user_id):
    user = authenticate(user_id)

    with Chat() as chat:
        messages = chat.read(250)

    return render_template('messages.html', messages=messages, user=user)


@app.route("/archiv/<user_id>")
def archive(user_id):
    user = authenticate(user_id)

    with Chat() as chat:
        messages = chat.read()

    return render_template('archive.html', messages=messages, user=user)


def authenticate(user_id):
    return User.find_by_user_id(user_id) or abort(404)


@app.url_defaults
def hashed_url_for_static_file(endpoint, values):
    create_hash(endpoint, values, app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
