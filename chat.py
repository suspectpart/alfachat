# -*- coding: utf-8 -*-
import alfachat as ac
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


@app.route("/<token>", methods=['POST', 'GET'])
def chat(token):
    try:
        user_uuid = uuid.UUID(token)
        user = ac.User(*config.users[user_uuid], uuid=user_uuid)
    except:
        return abort(404)

    if request.method == 'POST':
        message_string = request.form['message']
        message = ac.MessageParser().parse(user, escape(message_string))
        ac.write_chat(message.lines())

    return render_template('alfachat.html', user=user)


@app.route("/messages/<user_id>")
def messages(user_id):
    user_uuid = uuid.UUID(user_id)
    user = ac.User(*config.users[user_uuid], uuid=user_uuid)

    return render_template('messages.html', messages=ac.read_chat(), user=user)
