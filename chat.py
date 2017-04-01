# -*- coding: utf-8 -*-
import inspect
import messages
import sys

from models import *


def write(message):
    c = Chat()
    c.write(message)
    c.close()


def read(limit=-1):
    chat = Chat()
    messages = chat.read(limit)
    chat.close()

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
