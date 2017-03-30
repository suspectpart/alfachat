# -*- coding: utf-8 -*-
import config
import inspect
import json
import messages
import os
import re
import sys
import uuid
import users

from datetime import datetime
from store import Chat, Message

def write_lines(lines):
    with open(config.chatlog, 'w+') as f:
        for line in lines:
            f.write(str(line) + "\n")


def write(user, message, visible_to=None):

    m = Message(message, user, visible_to)
    c = Chat()
    c.write(m)
    c.close()

    #line = MessageLine(user, message, visible_to=visible_to)
    #with open(config.chatlog, 'a+') as f:
    #    f.write(str(line) + "\n")


def read(replace):
    pattern = re.compile(
        r"(https?:[\/\/|\\\\]+([\w\d:#@%\/;$()~_?\+-=\\\.&](#!)?)*)")
    replacement = r'<a href="\g<1>" target="_blank">\g<1></a>'
    messages = []

    if not os.path.isfile(config.chatlog):
        return []

    c = Chat()

    messages = c.read()
    c.close()
    
    return messages

def handle(user, message_string):
    for message_type in get_message_types():
        if message_type.handles(message_string):
            message_type(user, message_string).execute()
            return

    messages.PlainTextMessage(user, message_string).execute()


def get_message_types():
    types = inspect.getmembers(sys.modules[messages.__name__], inspect.isclass)
    return (t[1] for t in types if issubclass(t[1], messages.PlainTextMessage))