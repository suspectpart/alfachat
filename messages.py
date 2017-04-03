# -*- coding: utf-8 -*-
import config
import os
import inspect
import sys

from datetime import datetime as dt
from models import *


class MessageParser(object):

    def __init__(self):
        self.types = self.get_message_types()

    def parse(self, user, message_string):
        for message_type in self.types:
            if message_type.handles(message_string):
                return message_type(user, message_string).execute()

        return Message(message_string, user)

    def get_message_types(self):
        types = inspect.getmembers(sys.modules[__name__], inspect.isclass)

        return (t[1] for t in types if issubclass(t[1], BaseMessage))


class BaseMessage(object):
    def __init__(self):
        pass

    @staticmethod
    def handles(message):
        return False


class PrivateMessage(BaseMessage):

    """@&lt;user&gt; - Private Nachricht an @&lt;user&gt; senden"""

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user
        self.recipient = User.find_by_name(
            self.message_string.split()[0][1:])

    def execute(self):
        return Message(self.message_string, self.user, visible_to=[
            self.user, self.recipient])

    @staticmethod
    def handles(message):
        return Message.is_private(message)


class SmsMessage(BaseMessage):

    """/sms &lt;user&gt; &lt;text&gt;
    - SMS mit &lt;text&gt; an &lt;user&gt; versenden"""

    def __init__(self, user, message_string):
        self.user = user
        self.recipient = User.find_by_name(message_string.split()[1])
        self.text = " ".join(message_string.split()[2:])

    def execute(self):
        SMS(self.user, self.recipient, self.text).send()

        message = "SMS gesendet an {0}".format(self.recipient.username)

        return Message(message, User.alfabot(), visible_to=[self.user])

    @staticmethod
    def handles(message):
        return message.startswith("/sms")


class TrumpMessage(BaseMessage):

    """/trump - Letzten Tweet von @realDonaldTrump anzeigen"""

    def __init__(self, user, message_string):
        self.user = user

    def execute(self):
        tweet = TrumpTweet()

        if tweet.is_new():
            return Message(tweet.text, User.trump())
        else:
            return Message("You already did that. SAD!",
                           User.alfabot(), visible_to=[self.user])

    @staticmethod
    def handles(message):
        return message.startswith("/trump")


class AnnouncementMessage(BaseMessage):

    """/announce &lt;text&gt; - Öffentliche Kundmachung versenden"""

    def __init__(self, user, message_string):
        self.user = user
        self.message_string = message_string
        self.text = "<b>++++Öffentliche Kundmachung++++</b> <br/><br/>{0}"

    def execute(self):
        announcement_text = " ".join(self.message_string.split()[1:])
        message = self.text.format(announcement_text)
        return Message(message, User.alfabot())

    @staticmethod
    def handles(message):
        return message.startswith("/announce")


class AppointmentMessage(BaseMessage):

    """/termine - Thekentermine anzeigen"""

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user

    def execute(self):
        return Message(self.get_appointments(), User.alfabot(), visible_to=[self.user])

    def get_appointments(self):
        if os.path.isfile(config.appointments_path):
            with open(config.appointments_path, 'r') as f:
                return f.read().replace("\n", "   ")
        else:
            return "Keine Termine."

    @staticmethod
    def handles(message):
        return message.startswith("/termine")


class ShowsMessage(BaseMessage):

    """/shows - Liste aller anstehenden Shows"""

    def __init__(self, user, message_string):
        self.user = user

    def execute(self):
        if not os.path.isfile("shows.log"):
            return Message("Keine Shows", User.alfabot(), visible_to=[self.user])

        all_shows = []

        with open("shows.log", 'r') as shows:
            all_shows = [Show(s) for s in shows]

        all_shows = filter(lambda show: show.lies_in_past(), all_shows)
        all_shows = sorted(all_shows, key=lambda show: show.date)
        all_shows = [str(show) for show in all_shows]
        all_shows = "<b>Shows</b><br/><br/>" + "<br/>".join(all_shows)

        return Message(all_shows, User.alfabot(), visible_to=[self.user])

    @staticmethod
    def handles(message):
        return message.startswith("/shows")


class AddShowMessage(BaseMessage):

    """/addshow - Neue Show hinzufügen (dd.mm.yyyy bands location)"""

    def __init__(self, user, message_string):
        self.show = " ".join(message_string.split()[1:])
        self.message = "Show added: {0}".format(self.show)
        self.user = user

    def execute(self):
        if not self.parse_showdate():
            error_msg = "Unzulässiges Datumsformat (erwartet: dd.mm.yyyy)"
            return Message(error_msg, User.alfabot(), visible_to=[self.user])

        with open("shows.log", 'a+') as shows:
            shows.write(self.show + "\n")

        return Message(self.message, User.alfabot(), visible_to=[self.user])

    def parse_showdate(self):
        try:
            return dt.strptime(self.show.split()[0], '%d.%m.%Y')
        except ValueError:
            return None

    @staticmethod
    def handles(message):
        return message.startswith("/addshow")


class HelpMessage(BaseMessage):

    """/help - Diese Hilfe anzeigen"""

    def __init__(self, user, message_string):
        self.user = user

    def execute(self):
        help_text = "<b>Hilfe</b><br/><br/>"

        for message_type in MessageParser().types:
            doc_str = message_type.__doc__
            help_text += "{0}<br/>".format(doc_str) if doc_str else ""

        return Message(help_text, User.alfabot(), visible_to=[self.user])

    @staticmethod
    def handles(message):
        return message.startswith("/help")


class DeleteMessage(BaseMessage):
    """/delete - Die letzte Nachricht entfernen"""

    def __init__(self, user, message_string):
        self.user = user

    def execute(self):
        with Chat() as chat:
            chat.delete_latest_message_of(self.user)

        return None

    @staticmethod
    def handles(message):
        return message.startswith("/delete")


class ClearMessage(BaseMessage):
    """/clear - Entferne alle Messages vom Alfabot"""

    def __init__(self, user, message_string):
        self.user = user

    def execute(self):
        with Chat() as chat:
            chat.remove_bot_messages_for(self.user)

        return None

    @staticmethod
    def handles(message):
        return message.startswith("/clear")
