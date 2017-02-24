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


def write_lines(lines):
    with open(config.chatlog, 'w+') as f:
        for line in lines:
            f.write(str(line) + "\n")


def write(user, message, visible_to=None):
    line = MessageLine(user, message, visible_to=visible_to)
    with open(config.chatlog, 'a+') as f:
        f.write(str(line) + "\n")


def read(replace):
    pattern = re.compile(
        r"(https?:[\/\/|\\\\]+([\w\d:#@%\/;$()~_?\+-=\\\.&](#!)?)*)")
    replacement = r'<a href="\g<1>" target="_blank">\g<1></a>'
    messages = []

    if not os.path.isfile(config.chatlog):
        return []

    with open(config.chatlog, "r") as f:
        log = f.read().split("\n")
        for line in log:
            if line.strip():
                msgjson = MessageEncoder().decode(json.loads(line))
                if replace:
                    msgjson.message = re.sub(pattern, replacement, msgjson.message)
                messages.append(msgjson)

    return messages


def get_user_by_name(name):
    for user_id, values in config.users.items():
        if values[0] == name:
            return User(*values, uuid=user_id)
    return None


def get_user_by_uuid(uuid_str):
    user_uuid = uuid.UUID(uuid_str)

    try:
        return User(*config.users[user_uuid], uuid=user_uuid)
    except:
        return None


def handle(user, message_string):
    for message_type in get_message_types():
        if message_type.handles(message_string):
            message_type(user, message_string).execute()
            return

    messages.PlainTextMessage(user, message_string).execute()


def get_message_types():
    types = inspect.getmembers(sys.modules[messages.__name__], inspect.isclass)
    return (t[1] for t in types if issubclass(t[1], messages.PlainTextMessage))


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

        return MessageLine(
                user, obj["message"], obj["timestamp"], obj["visible_to"])


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


bot = User("alfabot", "gray", "", None)
