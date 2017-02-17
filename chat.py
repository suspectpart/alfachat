# -*- coding: utf-8 -*-
import alfachat as ac
import config
import logging
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
def chat(token):
    try:
        user = ac.User(*config.users[uuid.UUID(token)])
    except:
        return abort(404)

    if request.method == 'POST':
        message_string = request.form['message']
        message = ac.MessageParser().parse(user, escape(message_string))
        ac.write_chat(message.lines())

    return render_template('alfachat.html', user=user.username, user_id=uuid.UUID(token))


@app.route("/messages/<user_id>")
def messages(user_id):
    user = ac.User(*config.users[uuid.UUID(user_id)]).username

    return render_template('messages.html', messages=ac.read_chat(), user=user)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, use_reloader=False, threaded=True)
