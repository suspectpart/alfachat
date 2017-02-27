# -*- coding: utf-8 -*-
import chat
import config
import os
import requests
import bs4
import users

from datetime import datetime as dt


class PlainTextMessage(object):

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user

    def execute(self):
        chat.write(self.user, self.message_string)

    @staticmethod
    def handles(message):
        return False


class SmsMessage(PlainTextMessage):

    """@bot sms &lt;user&gt; &lt;text&gt;
    - SMS mit &lt;text&gt; an &lt;user&gt; versenden"""

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user
        self.recipient = users.find_by_name(self.message_string.split()[2])

    def execute(self):
        sms_text = " ".join(self.message_string.split()[3:])
        sms_text = "[{0}] {1}".format(self.user.username, sms_text)
        message = "SMS sent to {0}".format(self.recipient.username)

        self.send_sms_to(self.recipient.number, sms_text)
        chat.write(users.bot, message, visible_to=[
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


class TrumpMessage(PlainTextMessage):

    """@bot trump - Letzten Tweet von @realDonaldTrump anzeigen"""

    def __init__(self, user, message_string):
        self.user = user
        self.trump = users.User("trump", "orange", "", None)

    def execute(self):
        html = requests.get("https://mobile.twitter.com/realDonaldTrump").text
        soup = bs4.BeautifulSoup(html, 'html5lib')
        tweet = soup.find('div', 'tweet-text').div.text.strip()
        if self.tweet_is_new(tweet):
            chat.write(self.trump, tweet)
        else:
            chat.write(users.bot, "You already did that. SAD!",
                       visible_to=[self.user.username])

    def tweet_is_new(self, tweet):
        with open(".trump", "a+") as f:
            f.seek(0)
            if f.read() == tweet:
                return False
            f.truncate()
            f.write(tweet)
            return True

    @staticmethod
    def handles(message):
        return message.startswith("@bot trump")


class AnnouncementMessage(PlainTextMessage):

    """@bot announce &lt;text&gt; - Öffentliche Kundmachung versenden"""

    def __init__(self, user, message_string):
        self.user = user
        self.message_string = message_string
        self.text = "<b>++++Öffentliche Kundmachung++++</b> <br/><br/>{0}"

    def execute(self):
        announcement_text = " ".join(self.message_string.split()[2:])
        message = self.text.format(announcement_text)
        chat.write(users.bot, message)

    @staticmethod
    def handles(message):
        return message.startswith("@bot announce")


class AppointmentMessage(PlainTextMessage):

    """@bot termine - Thekentermine anzeigen"""

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user

    def execute(self):
        chat.write(users.bot, self.get_appointments())

    def get_appointments(self):
        if os.path.isfile(config.appointments_path):
            with open(config.appointments_path, 'r') as f:
                return f.read().replace("\n", "   ")
        else:
            return "Keine Termine."

    @staticmethod
    def handles(message):
        return message.startswith("@bot termine")


class PrivateMessage(PlainTextMessage):

    """@&lt;user&gt; - Private Nachricht an @&lt;user&gt; senden"""

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user
        self.recipient = users.find_by_name(
            self.message_string.split()[0][1:])

    def execute(self):
        chat.write(self.user, self.message_string, visible_to=[
                   self.user.username, self.recipient.username])

    @staticmethod
    def handles(message):
        return bool(users.find_by_name(message.split()[0][1:]))


class ShowsMessage(PlainTextMessage):

    """@bot shows - Liste aller anstehenden Shows"""

    def __init__(self, user, message_string):
        self.user = user

    def execute(self):
        if not os.path.isfile("shows.log"):
            chat.write(
                users.bot, "Keine Shows", visible_to=[self.user.username])
            return

        all_shows = []

        with open("shows.log", 'r') as shows:
            all_shows = [Show(s) for s in shows]

        all_shows = filter(lambda show: show.lies_in_past(), all_shows)
        all_shows = sorted(all_shows, key=lambda show: show.date)
        all_shows = [str(show) for show in all_shows]
        all_shows = "<b>Shows</b><br/><br/>" + "<br/>".join(all_shows)

        chat.write(users.bot, all_shows, visible_to=[self.user.username])

    @staticmethod
    def handles(message):
        return message.startswith("@bot shows")


class Show(object):

    def __init__(self, show_str):
        self.show_str = show_str.strip()
        self.date = dt.strptime(self.show_str.split()[0], '%d.%m.%Y')

    def lies_in_past(self):
        return self.date >= dt.today()

    def __str__(self):
        return self.show_str


class AddShowMessage(PlainTextMessage):

    """@bot addshow - Neue Show hinzufügen (dd.mm.yyyy bands location)"""

    def __init__(self, user, message_string):
        self.show = " ".join(message_string.split()[2:])
        self.message = "Show added: {0}".format(self.show)
        self.user = user

    def execute(self):
        if not self.parse_showdate():
            error_msg = "Invalid date format (must be dd.mm.yyyy)"
            chat.write(users.bot, error_msg, visible_to=[self.user.username])
            return

        with open("shows.log", 'a+') as shows:
            shows.write(self.show + "\n")

        chat.write(users.bot, self.message, visible_to=[self.user.username])

    def parse_showdate(self):
        try:
            return dt.strptime(self.show.split()[0], '%d.%m.%Y')
        except:
            return None

    @staticmethod
    def handles(message):
        return message.startswith("@bot addshow")


class HelpMessage(PlainTextMessage):

    """@bot help - Diese Hilfe anzeigen"""

    def __init__(self, user, message_string):
        self.user = user

    def execute(self):
        help_text = "<b>Hilfe</b><br/><br/>"

        for message_type in chat.get_message_types():
            doc_str = message_type.__doc__
            help_text += "{0}<br/>".format(doc_str) if doc_str else ""

        chat.write(users.bot, help_text, visible_to=[self.user.username])

    @staticmethod
    def handles(message):
        return message.startswith("@bot help")


class DeleteMessage(PlainTextMessage):
    """@bot delete - Die letzte Nachricht entfernen"""

    def __init__(self, user, message_string):
        self.user = user

    def execute(self):
        lines = chat.read(False)
        lines.reverse()
        remove_entry = None
        for l in lines:
            if l.user == self.user.username:
                remove_entry = l
                break
        if remove_entry:
            lines.remove(remove_entry)
            lines.reverse()
            chat.write_lines(lines)

    @staticmethod
    def handles(message):
        return message.startswith("@bot delete")
