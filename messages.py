import alfachat as ac
import config
import inspect
import os
import sys


class SmsMessage(object):
    """@bot sms &lt;user&gt; &lt;text&gt; - SMS mit &lt;text&gt; an &lt;user&gt; versenden"""
    
    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user
        self.recipient = ac.get_user_by_name(self.message_string.split()[2])

    def lines(self):
        lines = []

        sms_text = self.message_string.split()[3:]

        lines.append(ac.MessageLine("alfabot", "SMS sent to {0}".format(self.recipient.username), "gray",
                                 visible_to=[self.user.username, self.recipient.username]))
        ac.send_sms_to(config.sms_config, self.recipient.number, "[{0}] ".format(self.user.username) + " ".join(sms_text))

        return lines
        
    @staticmethod
    def handles(message):
        return message.startswith("@bot sms")


class TrumpMessage(object):
    """@bot trump - Letzten Tweet von @realDonaldTrump anzeigen"""
    
    def __init__(self, user, message_string):
        pass

    def lines(self):
        tweet = ac.get_latest_trump_tweet()
        return [ac.MessageLine("trump", tweet, "orange")]

    @staticmethod
    def handles(message):
        return message.startswith("@bot trump")

        
class AnnouncementMessage(object):
    """@bot announce &lt;text&gt; - Öffentliche Kundmachung versenden"""
    
    def __init__(self, user, message_string):
        self.user = user
        self.message_string = message_string

    def lines(self):
        announcement_text = " ".join(self.message_string.split()[2:])
        message = "<b>++++Öffentliche Kundmachung++++</b> <br/><br/>{0}".format(announcement_text)
        return [ac.MessageLine("alfabot", message, "gray")]

    @staticmethod
    def handles(message):
        return message.startswith("@bot announce")

        
class AppointmentMessage(object):
    """@bot termine - Thekentermine anzeigen"""

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user

    def lines(self):
        return [ac.MessageLine("alfabot", ac.get_appointments(), "gray")]

    @staticmethod
    def handles(message):
        return message.startswith("@bot termine")

        
class PrivateMessage(object):
    """@&lt;user&gt; - Private Nachricht an @&lt;user&gt; senden"""

    def __init__(self, user, message_string):
        self.message_string = message_string
        self.user = user
        self.recipient = ac.get_user_by_name(self.message_string.split()[0][1:])

    def lines(self):
        return [ac.MessageLine(self.user.username, self.message_string, self.user.color,
                            visible_to=[self.user.username, self.recipient.username])]

    @staticmethod
    def handles(message):
        return any([message.startswith("@{0}".format(v[0])) for _, v in config.users.items()])

        
class ShowsMessage(object):
    """@bot shows - Liste aller anstehenden Shows"""
    
    def __init__(self, user, message_string):
        pass

    def lines(self):
        if not os.path.isfile("shows.log"):
            return [ac.MessageLine("alfabot", "Keine Shows", "gray")]

        all_shows = "<b>Shows</b><br/><br/>"

        with open("shows.log", 'r') as shows:
            for show in shows:
                all_shows += "{0}<br/>".format(show)

        return [ac.MessageLine("alfabot", all_shows, "gray")]

    @staticmethod
    def handles(message):
        return message.startswith("@bot shows")
        
    
class HelpMessage(object):
    """@bot help - Diese Hilfe anzeigen"""

    def __init__(self, user, message_string):
        self.user = user

    def lines(self):
        help_text = "<b>Hilfe</b><br/><br/>"
        
        message_types = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        
        for message_type in message_types:
            help_text += "{0}<br/>".format(message_type[1].__doc__)

        return [ac.MessageLine("alfabot", help_text, "gray", visible_to=[self.user.username])]
        
    @staticmethod
    def handles(message):
        return message.startswith("@bot help")