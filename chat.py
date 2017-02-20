# -*- coding: utf-8 -*-
import config
import inspect
import json
import messages
import os
import re
import sys
import uuid

from datetime import datetime


def write(user, message, visible_to=None):
    line = MessageLine(user, message, visible_to=visible_to)
    with open("chat.log", 'a+') as f:
        f.write(str(line) + "\n")


def read():
    pattern = re.compile(
        r"(https?:[\/\/|\\\\]+([\w\d:#@%\/;$()~_?\+-=\\\.&](#!)?)*)")
    replacement = r'<a href="\g<1>" target="_blank">\g<1></a>'
    messages = []

    if not os.path.isfile("chat.log"):
        return []

    with open("chat.log", "r") as f:
        log = f.read().split("\n")
        for line in log:
            if line.strip():
                msgjson = MessageEncoder().decode(json.loads(line))
                msgjson.message = re.sub(pattern, replacement, msgjson.message)
                messages.append(msgjson)

    return messages


def get_user_by_name(name):
    for uuid, values in config.users.items():
        if values[0] == name:
            return User(*values, uuid=uuid)
    return None


def get_user_by_uuid(uuid_str):
    user_uuid = uuid.UUID(uuid_str)

    try:
        return User(*config.users[user_uuid], uuid=user_uuid)
    except:
        return None


class MessageEncoder(json.JSONEncoder):

    def default(self, message):
        if isinstance(message, MessageLine):
            return {"user": message.user,
                    "message": message.message,
                    "color": message.color,
                    "timestamp": str(message.timestamp),
                    "visible_to": message.visible_to}

        return json.JSONEncoder.default(self, message)

    def decode(self, obj):
        user = get_user_by_name(obj["user"])
        if not user:
            user = User(obj["user"], obj["color"], "", None)
        return MessageLine(user, obj["message"], obj["timestamp"], obj["visible_to"])


class MessageLine(object):

    def __init__(self, user, message, timestamp=None, visible_to=None):
        self.user = user.username
        self.color = user.color
        self.message = message
        self.timestamp = timestamp if timestamp else datetime.now()
        self.visible_to = visible_to or []

    def __str__(self):
        return MessageEncoder().encode(self)


class User(object):

    def __init__(self, username, color, number, uuid):
        self.username = username
        self.color = color
        self.number = number
        self.uuid = uuid


class Bot(User):

    def __init__(self):
        self.username = "alfabot"
        self.color = "gray"
        self.number = ""
        self.uuid = None


class MessageParser(object):

    def __init__(self):
        pass

    def parse(self, user, message_string):
        message_types = inspect.getmembers(
            sys.modules[messages.__name__], inspect.isclass)

        message_types = filter(
            lambda mt: issubclass(mt[1], messages.PlainTextMessage), message_types)

        for message_type in message_types:
            class_ = message_type[1]

            if class_.handles(message_string):
                return class_(user, message_string)

        return messages.PlainTextMessage(user, message_string)
