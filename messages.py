# -*- coding: utf-8 -*-
import chat
import config
import inspect
import os
import requests
import sys
import bs4


class SmsMessage(object):

    """@bot sms &lt;user&gt; &lt;text&gt;
    - SMS mit &lt;text&gt; an &lt;user&gt; versenden"""

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user
        self.recipient = chat.get_user_by_name(self.message_string.split()[2])

    def execute(self):
        sms_text = " ".join(self.message_string.split()[3:])
        sms_text = "[{0}] {1}".format(self.user.username, sms_text)
        message = "SMS sent to {0}".format(self.recipient.username)

        self.send_sms_to(self.recipient.number, sms_text)
        chat.write(chat.Bot(), message, visible_to=[
                   self.user.username, self.recipient.username])

    def send_sms_to(self, number, text):
        url = "https://www.smsout.de/client/sendsms.php"
        query = "?Username={0}&Password={1}&SMSTo={2}&SMSType=V1&SMSText={3}"

        user, password = config.sms_config

        request_url = url + query.format(user, password, number, text)
        print(request_url)
        return requests.get(request_url)

    @staticmethod
    def handles(message):
        return message.startswith("@bot sms")


class TrumpMessage(object):

    """@bot trump - Letzten Tweet von @realDonaldTrump anzeigen"""

    def __init__(self, user, message_string):
        self.trump = chat.User("trump", "orange", "", None)

    def execute(self):
        html = requests.get("https://mobile.twitter.com/realDonaldTrump").text
        soup = bs4.BeautifulSoup(html, 'html5lib')
        tweet = soup.find('div', 'tweet-text').div.text.strip()
        chat.write(self.trump, tweet)

    @staticmethod
    def handles(message):
        return message.startswith("@bot trump")


class AnnouncementMessage(object):

    """@bot announce &lt;text&gt; - Öffentliche Kundmachung versenden"""

    def __init__(self, user, message_string):
        self.user = user
        self.message_string = message_string
        self.text = "<b>++++Öffentliche Kundmachung++++</b> <br/><br/>{0}"

    def execute(self):
        announcement_text = " ".join(self.message_string.split()[2:])
        message = self.text.format(announcement_text)
        chat.write(chat.Bot(), message)

    @staticmethod
    def handles(message):
        return message.startswith("@bot announce")


class AppointmentMessage(object):

    """@bot termine - Thekentermine anzeigen"""

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user

    def execute(self):
        chat.write(chat.Bot(), self.get_appointments())

    def get_appointments(self):
        if os.path.isfile(config.appointments_path):
            with open(config.appointments_path, 'r') as f:
                return f.read().replace("\n", "   ")
        else:
            return "Keine Termine."

    @staticmethod
    def handles(message):
        return message.startswith("@bot termine")


class PrivateMessage(object):

    """@&lt;user&gt; - Private Nachricht an @&lt;user&gt; senden"""

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user
        self.recipient = chat.get_user_by_name(
            self.message_string.split()[0][1:])

    def execute(self):
        chat.write(self.user, self.message_string, visible_to=[
                   self.user.username, self.recipient.username])

    @staticmethod
    def handles(message):
        return any([message.startswith("@{0}".format(v[0])) for _, v in config.users.items()])


class ShowsMessage(object):

    """@bot shows - Liste aller anstehenden Shows"""

    def __init__(self, user, message_string):
        self.user = user

    def execute(self):
        if not os.path.isfile("shows.log"):
            chat.write(
                chat.Bot(), "Keine Shows", visible_to=[self.user.username])
            return

        all_shows = "<b>Shows</b><br/><br/>"

        with open("shows.log", 'r') as shows:
            for show in shows:
                all_shows += "{0}<br/>".format(show)

        chat.write(chat.Bot(), all_shows, visible_to=[self.user.username])

    @staticmethod
    def handles(message):
        return message.startswith("@bot shows")


class AddShowMessage(object):

    """@bot addshow - Neue Show hinzufügen (dd.mm.yyyy bands location)"""

    def __init__(self, user, message_string):
        self.show = " ".join(message_string.split()[2:])
        self.message = "Show added: {0}".format(self.show)
        self.user = user

    def execute(self):
        with open("shows.log", 'a+') as shows:
            shows.write(self.show + "\n")

        chat.write(chat.Bot(), self.message, visible_to=[self.user.username])

    @staticmethod
    def handles(message):
        return message.startswith("@bot addshow")


class HelpMessage(object):

    """@bot help - Diese Hilfe anzeigen"""

    def __init__(self, user, message_string):
        self.user = user

    def execute(self):
        help_text = "<b>Hilfe</b><br/><br/>"

        messages = inspect.getmembers(sys.modules[__name__], inspect.isclass)

        for message_type in messages:
            help_text += "{0}<br/>".format(message_type[1].__doc__)

        chat.write(chat.Bot(), help_text, visible_to=[self.user.username])

    @staticmethod
    def handles(message):
        return message.startswith("@bot help")
