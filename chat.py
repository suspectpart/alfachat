# -*- coding: utf-8 -*-
import inspect
import messages
import re
import sys

from models import *

pattern = re.compile(
    r"(https?:[\/\/|\\\\]+([\w\d:#@%\/;$()~_?\+-=\\\.&](#!)?)*)")

repl = r'<a href="\g<1>" target="_blank">\g<1></a>'


def write(message):
    c = Chat()
    c.write(message)
    c.close()


def read():
    chat = Chat()
    messages = chat.read()
    chat.close()

    for message in messages:
        message.text = re.sub(pattern, repl, message.text)

    return messages


def handle(user, message_string):
    for message_type in get_message_types():
        if message_type.handles(message_string):
            write(message_type(user, message_string).execute())
            return

    write(messages.PlainTextMessage(user, message_string).execute())


def get_message_types():
    types = inspect.getmembers(sys.modules[messages.__name__], inspect.isclass)
    return (t[1] for t in types if issubclass(t[1], messages.PlainTextMessage))
