# -*- coding: utf-8 -*-
import chat
import config
import uuid
from flask import abort
from flask import escape
from flask import Flask
from flask import request
from flask import render_template
from flask import send_from_directory

app = Flask(__name__, static_folder='static', static_url_path='')


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route("/<token>", methods = ['POST', 'GET'])
def token(token):
    try:
        user_uuid = uuid.UUID(token)
        user = chat.User(*config.users[user_uuid], uuid = user_uuid)
    except:
        return abort(404)

    if request.method == 'POST':
        message_string = request.form['message']
        message = chat.MessageParser().parse(user, escape(message_string))
        message.execute()

    return render_template('alfachat.html', user = user)


@app.route("/messages/<user_id>")
def messages(user_id):
    user_uuid = uuid.UUID(user_id)
    user = chat.User(*config.users[user_uuid], uuid = user_uuid)

    return render_template('messages.html', messages = chat.read(), user = user)


if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 8080)