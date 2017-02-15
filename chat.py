# -*- coding: utf-8 -*-
import alfachat as ac
import config
import json
import logging
import os
import re
import uuid
from flask import abort
from flask import escape
from flask import Flask
from flask import request
from flask import render_template
from flask import send_from_directory

app = Flask(__name__, static_folder='static', static_url_path='')

# log stuff
logger = logging.getLogger('werkzeug')
handler = logging.FileHandler('access.log')
logger.addHandler(handler)
app.logger.addHandler(handler)


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route("/<token>", methods=['POST', 'GET'])
def hello(token):
    try:
        user = ac.User(*config.users[uuid.UUID(token)])
    except:
        return abort(404)

    if request.method == 'POST':
        message_string = escape(request.form['message'])
        message = ac.MessageParser().parse(user, message_string)
        ac.persist(message.lines())

    return render_template('alfachat.html', user=user.username, user_id=uuid.UUID(token))


@app.route("/messages/<user_id>")
def messages(user_id):
    user = ac.User(*config.users[uuid.UUID(user_id)]).username

    pattern = re.compile(r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)')

    if os.path.isfile("chat.log"):
        with open("chat.log", "r") as f:
            log = f.read().split("\n")
            for line in log:
                if line.strip():
                    msg_json = ac.MessageEncoder().decode(json.loads(line))
                    msg_json.message = re.sub(pattern, r'<a href="\g<1>" target="_blank">\g<1></a>', msg_json.message)
                    messages.append(msg_json)

    return render_template('messages.html', messages=messages, user=user)


if __name__ == "__main__":
    while True:
        try:
            app.run(host='0.0.0.0', port=8080, use_reloader=False, threaded=True)
        except:
            pass
