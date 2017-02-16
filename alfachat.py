import config
import inspect
import json
import os
import re
import requests
import sys
import messages

from bs4 import BeautifulSoup
from datetime import datetime


def get_latest_trump_tweet():
    html = requests.get("http://twitter.com/realDonaldTrump").text
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find('div', 'js-tweet-text-container').p.text
    

def send_sms_to(sms_config, number, text):
    url = "https://www.smsout.de/client/sendsms.php?Username={0}&Password={1}&SMSTo={2}&SMSType=V1&SMSText={3}"
    return requests.get(url.format(sms_config[0], sms_config[1], number, text))


def write_chat(message_lines):
    with open("chat.log", 'a+') as f:
        for line in message_lines:
            f.write(str(line) + "\n")


def read_chat():
    pattern = re.compile(r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)')

    messages = []

    if not os.path.isfile("chat.log"):
        return []

    with open("chat.log", "r") as f:
        log = f.read().split("\n")
        for line in log:
            if line.strip():
                msg_json = MessageEncoder().decode(json.loads(line))
                msg_json.message = re.sub(pattern, r'<a href="\g<1>" target="_blank">\g<1></a>', msg_json.message)
                messages.append(msg_json)

    return messages


def get_user_by_name(name):
    return User(*(list(filter(lambda u: u[0] == name, config.users.values()))[0]))


def get_appointments():
    if os.path.isfile(config.appointments_path):
        with open(config.appointments_path, 'r') as f:
            return f.read().replace("\n", "   ")
    else:
        return "Keine Termine."


class MessageEncoder(json.JSONEncoder):
    def default(self, message):
        if isinstance(message, MessageLine):
            return {"user": message.user, "message": message.message, "color": message.color,
                    "timestamp": str(message.timestamp), "visible_to": message.visible_to}

        return json.JSONEncoder.default(self, message)

    def decode(self, obj):
        return MessageLine(obj["user"], obj["message"], obj["color"], obj["timestamp"], obj["visible_to"])


class MessageLine(object):
    def __init__(self, user, message, color, timestamp=None, visible_to=None):
        self.user = user
        self.message = message
        self.color = color
        self.timestamp = timestamp if timestamp else datetime.now()
        self.visible_to = visible_to if visible_to else []

    def __str__(self):
        return MessageEncoder().encode(self)

        
class User(object):
    def __init__(self, username, color, number):
        self.username = username
        self.color = color
        self.number = number

        
class PlainTextMessage(object):
    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user

    def lines(self):
        return [MessageLine(self.user.username, self.message_string, self.user.color)]

    @staticmethod
    def handles(message):
        return True


class MessageParser(object):
    def __init__(self):
        pass

    def parse(self, user, message_string):
        message_types = inspect.getmembers(sys.modules[messages.__name__], inspect.isclass)
        
        for message_type in message_types:
            class_ = message_type[1]
            
            if class_.handles(message_string):
                return class_(user, message_string)
                
        return PlainTextMessage(user, message_string)