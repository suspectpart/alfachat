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


@app.route("/<user_id>", methods=['POST', 'GET'])
def token(user_id):
    user = chat.get_user_by_uuid(user_id) or abort(404)

    if request.method == 'POST':
        message_string = request.form['message']
        chat.MessageParser().parse(user, escape(message_string)).execute()

    return render_template('alfachat.html', user=user)


@app.route("/messages/<user_id>")
def messages(user_id):
    user = chat.get_user_by_uuid(user_id) or abort(404)

    return render_template('messages.html', messages=chat.read(), user=user)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
