 # -*- coding: utf-8 -*-
import config
import json
import logging
import os
import re
import requests
import uuid
from datetime import datetime
from flask import abort
from flask import escape
from flask import Flask
from flask import request
from flask import render_template

app = Flask(__name__)

# log stuff
logger = logging.getLogger('werkzeug')
handler = logging.FileHandler('access.log')
logger.addHandler(handler)
app.logger.addHandler(handler)

def send_sms_to(number, text):
    return requests.get("https://www.smsout.de/client/sendsms.php?Username={0}&Password={1}&SMSTo={2}&SMSType=V1&SMSText={3}".format(config.sms_config[0], config.sms_config[1], number, text))
    
class Message(object):
    def __init__(self, user, message, color, timestamp = None, visible_to = []):
        self.user = user
        self.message = message
        self.color = color
        self.timestamp = timestamp if timestamp else datetime.now()
        self.visible_to = visible_to
        
    def __str__(self):
        return MessageEncoder().encode(self)

class MessageEncoder(json.JSONEncoder):
    def default(self, message):
        if isinstance(message, Message):
            return {"user": message.user, "message": message.message, "color": message.color, "timestamp": str(message.timestamp), "visible_to": message.visible_to}

        return json.JSONEncoder.default(self, obj)    
    
    def decode(message, obj):
        return Message(obj["user"], obj["message"], obj["color"], obj["timestamp"], obj["visible_to"])

def get_appointments():
    if os.path.isfile(config.appointments_path):
        with open(config.appointments_path, 'r') as f:
            return f.read().replace("\n", "   ")
    else:
        return "Keine Termine."
        

@app.route("/robots.txt")
def robots():
    return "<pre>User-agent: *\nDisallow: /\n</pre>"

@app.route("/<token>", methods=['POST', 'GET'])
def hello(token):
    try:
        user, color, number = config.users[uuid.UUID(token)]
    except:
        abort(404)

    if request.method == 'POST':
        message = Message(user, escape(request.form['message']), color)
        
        if message.message =="::cls":
            with open("chat.log", 'w+') as f:
                f.write("")
                render_template('alfachat.html', user=user)

        
        with open("chat.log", 'a+') as f:
            for u in config.users.values():
                if message.message.startswith("@{0} ".format(u[0])):
                    message.visible_to = [user, u[0]]
                    
                if message.message.startswith("@bot sms {0}".format(u[0])):
                    message.visible_to = [user]
                    send_sms_to(u[2], "[{0}] ".format(user) + " ".join(message.message.split()[3:]))
            
            f.write(str(message) + "\n")
            
            if message.message == "@bot termine":
                f.write(str(Message("alfabot", get_appointments(), "gray")) + "\n")
   
    return render_template('alfachat.html', user=user, user_id=uuid.UUID(token))

@app.route("/messages/<user_id>")
def messages(user_id):
    log = ""
    messages = []
    
    user = config.users[uuid.UUID(user_id)][0]
 
    pattern = re.compile(r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)')

    if os.path.isfile("chat.log"):
        with open("chat.log", "r") as f:
            log = f.read().split("\n")
            for line in log:
                if line.strip():
                    msg_json = MessageEncoder().decode(json.loads(line))
                    msg_json.message = re.sub(pattern, r'<a href="\g<1>" target="_blank">\g<1></a>', msg_json.message)
                    messages.append(msg_json)
        
    return render_template('messages.html', messages=messages, user=user)


if __name__ == "__main__":
    while True:
        try:
            app.run(host='0.0.0.0', port=8080, use_reloader=False, threaded=True)
        except:
            pass
