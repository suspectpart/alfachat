import config
import json
import os
import requests
from datetime import datetime

def send_sms_to(sms_config, number, text):
    url = "https://www.smsout.de/client/sendsms.php?Username={0}&Password={1}&SMSTo={2}&SMSType=V1&SMSText={3}"
    return requests.get(url.format(sms_config[0], sms_config[1], number, text))

class MessageEncoder(json.JSONEncoder):
    def default(self, message):
        if isinstance(message, MessageLine):
            return {"user": message.user, "message": message.message, "color": message.color, "timestamp": str(message.timestamp), "visible_to": message.visible_to}

        return json.JSONEncoder.default(self, obj)    
    
    def decode(message, obj):
        return MessageLine(obj["user"], obj["message"], obj["color"], obj["timestamp"], obj["visible_to"])

class MessageLine(object):
    def __init__(self, user, message, color, timestamp = None, visible_to = []):
        self.user = user
        self.message = message
        self.color = color
        self.timestamp = timestamp if timestamp else datetime.now()
        self.visible_to = visible_to
        
    def __str__(self):
        return MessageEncoder().encode(self)

class PrivateMessage(object):
    def __init__(self, user, message_string):
        self.message_string = message_string

class AppointmentMessage(object):
    def __init__(self, user, message_string):
        self.message_string = message_string

class SmsMessage(object):
    def __init__(self, user, message_string):
        self.message_string = message_string

class PlainTextMessage(object):
    def __init__(self, user, message_string):
        self.message_string = message_string

class User(object):
    def __init__(self, username, color, number):
        self.username = username
        self.color = color
        self.number = number

class MessageParser(object):
    def __init__(self):
        pass

    def parse(self, user, message_string):
        if message.startswith("@bot termine"):
            return AppointmentMessage(user, message_string)
        if message.startswith("@bot sms"):
            return SmsMessage(user, message_string)
        if any([message.startswith("@{0}".format(v[0])) for _ ,v in config.users]):
            return PrivateMessage(user, message_string)
        return PlainTextMessage(user, message_string)

def get_appointments():
    if os.path.isfile(config.appointments_path):
        with open(config.appointments_path, 'r') as f:
            return f.read().replace("\n", "   ")
    else:
        return "Keine Termine."
