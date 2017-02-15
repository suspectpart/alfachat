import config
import json
import os
import re
import requests
from datetime import datetime


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


class SmsMessage(object):
    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user
        self.recipient = get_user_by_name(self.message_string.split()[2])

    def lines(self):
        lines = []

        sms_text = self.message_string.split()[3:]

        lines.append(MessageLine("alfabot", "SMS sent to {0}".format(self.recipient.username), "gray",
                                 visible_to=[self.user.username, self.recipient.username]))
        send_sms_to(config.sms_config, self.recipient.number, "[{0}] ".format(self.user.username) + " ".join(sms_text))

        return lines


class AnnouncementMessage(object):
    def __init__(self, user, message_string):
        self.user = user
        self.message_string = message_string

    def lines(self):
        announcement_text = " ".join(self.message_string.split()[2:])
        message = "<b>++++Öffentliche Kundmachung++++</b> <br/><br/>{0}".format(announcement_text)
        return [MessageLine("alfabot", message, "gray")]


class AppointmentMessage(object):
    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user

    def lines(self):
        return [MessageLine("alfabot", get_appointments(), "gray")]


class PlainTextMessage(object):
    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user

    def lines(self):
        return [MessageLine(self.user.username, self.message_string, self.user.color)]


class PrivateMessage(object):
    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user
        self.recipient = get_user_by_name(self.message_string.split()[0][1:])

    def lines(self):
        return [MessageLine(self.user.username, self.message_string, self.user.color,
                            visible_to=[self.user.username, self.recipient.username])]


class ShowsMessage(object):
    def __init__(self):
        pass

    def lines(self):
        if not os.path.isfile("shows.log"):
            return [MessageLine("alfabot", "Keine Shows", "gray")]

        all_shows = "<b>Shows</b><br/><br/>"

        with open("shows.log", 'r') as shows:
            for show in shows:
                all_shows += "{0}<br/>".format(show)

        return [MessageLine("alfabot", all_shows, "gray")]


class HelpMessage(object):
    def __init__(self, user):
        self.user = user

    def lines(self):
        help_text = "<b>Hilfe</b><br/><br/> \
            @&lt;user&gt; - Private Nachricht an &lt;user&gt; schreiben <br/><br /> \
            @bot announce &lt;text&gt; - Öffentliche Kundmachung versenden <br/> \
            @bot sms &lt;user&gt; &lt;text&gt; - SMS mit &lt;text&gt; an &lt;user&gt; versenden <br/> \
            @bot termine - Thekentermine anzeigen<br/> \
            @bot shows - Zeige nächste Konzerte<br/> \
            @bot help - Diese Hilfe anzeigen <br/>"

        return [MessageLine("alfabot", help_text, "gray", visible_to=[self.user.username])]


class User(object):
    def __init__(self, username, color, number):
        self.username = username
        self.color = color
        self.number = number


class MessageParser(object):
    def __init__(self):
        pass

    def parse(self, user, message_string):
        if message_string.startswith("@bot termine"):
            return AppointmentMessage(user, message_string)
        if message_string.startswith("@bot sms"):
            return SmsMessage(user, message_string)
        if message_string.startswith("@bot help"):
            return HelpMessage(user)
        if message_string.startswith("@bot announce"):
            return AnnouncementMessage(user, message_string)
        if message_string.startswith("@bot shows"):
            return ShowsMessage()
        if any([message_string.startswith("@{0}".format(v[0])) for _, v in config.users.items()]):
            return PrivateMessage(user, message_string)
        return PlainTextMessage(user, message_string)
