import bs4
import config
import re
import requests
import sqlite3

from datetime import datetime
from uuid import UUID

PATH = "chat.sqlite"


class Show(object):

    def __init__(self, show_str):
        self.show_str = show_str.strip()
        self.date = datetime.strptime(self.show_str.split()[0], '%d.%m.%Y')

    def lies_in_past(self):
        return self.date >= datetime.today()

    def __str__(self):
        return self.show_str


class TrumpTweet(object):

    def __init__(self):
        html = requests.get("https://mobile.twitter.com/realDonaldTrump").text
        soup = bs4.BeautifulSoup(html, 'lxml')
        self.text = soup.find('div', 'tweet-text').div.text.strip()

    def is_new(self):
        with open(".trump", "a+") as f:
            f.seek(0)
            last_tweet = f.read()
            f.truncate()
            f.write(self.text)
            f.flush()
        return last_tweet != self.text


class SMS(object):
    url = "https://www.smsout.de/client/sendsms.php"
    query = "?Username={0}&Password={1}&SMSTo={2}&SMSType=V1&SMSText={3}"

    def __init__(self, sender, recipient, text):
        self.sender = sender
        self.recipient = recipient
        self.text = text

    def send(self):
        sms_text = "[{0}] {1}".format(self.sender.username, self.text)

        user, password = config.sms_config
        number = self.recipient.number

        url = self.url + self.query.format(user, password, number, sms_text)

        print(url)

        return requests.get(url)


class Users(object):
    users = []

    def __init__(self):
        self._connection = sqlite3.connect(PATH)
        self._initialize_database()
        self.users = self.users or self.all()

    def _initialize_database(self):
        sql = """create table if not exists users (
            id integer primary key not null,
            name text not null,
            user_id text not null unique,
            color text not null,
            number text
        )"""

        self._execute(sql)
        self._connection.commit()

    def all(self):
        result = self._execute("""select * from users""")

        return [User(r[1], r[3], r[4], UUID(r[2])) for r in result]

    def find_by_name(self, name):
        matches = list(filter(lambda u: u.username == name, self.users))
        return matches[0] if matches else None

    def find_by_user_id(self, uuid_str):
        matches = list(filter(lambda u: str(u.user_id) == uuid_str,
                              self.users))
        return matches[0] if matches else None

    def exists(self, user):
        return self.find_by_user_id(user.user_id) is not None

    def insert(self, user):
        sql = """insert into users
            (name, user_id, color, number)
            values (?, ?, ?, ?)
        """

        try:
            self._execute(sql, (user.username, str(
                user.user_id), user.color, user.number))
            self._connection.commit()

            # update users after insert
            self.users = self.all()

            return True
        except sqlite3.IntegrityError:
            return False

    def trump(self):
        return self.find_by_name("trump")

    def alfabot(self):
        return self.find_by_name("alfabot")

    def _execute(self, sql, params=()):
        return self._connection.cursor().execute(sql, params)


class User(object):

    def __init__(self, username, color, number, uuid):
        self.username = username
        self.color = color
        self.number = number
        self.user_id = uuid

    def exists(self):
        return Users().exists(self)

    def save(self):
        return Users().insert(self)

    def __str__(self):
        return str(self.user_id)

    def __eq__(self, other):
        return other and (self.user_id == other.user_id)

    __repr__ = __str__


class Message:

    pattern = re.compile(
        r"(https?:[\/\/|\\\\]+([\w\d:#@%\/;$()~_?\+-=\\\.&](#!)?)*)")

    repl = r'<a href="\g<1>" target="_blank">\g<1></a>'

    def __init__(self, message_text, user, visible_to=None, pk=-1):
        self.user = user
        self.text = message_text
        self.visible_to = visible_to or []
        self.is_private = Message.is_private(self.text)
        self.pk = pk

    def html_text(self):
        return re.sub(self.pattern, self.repl, self.text)

    @staticmethod
    def is_private(message):
        starts_with_at = message.startswith("@")
        followed_by_user = bool(Users().find_by_name(message.split()[0][1:]))

        return starts_with_at and followed_by_user

    def __str__(self):
        return "[{0}] {1} (visible to {2})".format(
            self.user.username,
            self.text, ",".join(map(str, self.visible_to)))

    def is_visible_to(self, user):
        return (not self.visible_to) or (user in self.visible_to)

    def to_json(self):
        return """{{"text":"{0}",
                    "pk":"{1}",
                    "user":"{2}",
                    "color":"{3}",
                    "private":{4}}}""".format(
            self.text, self.pk, self.user.username,
            self.user.color, str(self.is_private).lower())


class Chat(object):

    def __init__(self):
        self._connection = sqlite3.connect(PATH)
        self._initialize_database()

    def close(self):
        self._connection.commit()
        self._connection.close()

    def _execute(self, sql, params=()):
        return self._connection.cursor().execute(sql, params)

    def _initialize_database(self):
        sql = """create table if not exists chat (
            id integer primary key not null,
            message text not null,
            user_id text not null,
            visible_to text not null,
            timestamp datetime default current_timestamp
        )"""

        self._execute(sql)
        self._connection.commit()

    def write(self, message):
        if not message:
            return

        sql = """insert into chat (message, user_id, visible_to)
            values (?, ?, ?)"""

        visible_to = ",".join(map(str, message.visible_to))

        self._execute(sql, (message.text, str(
            message.user.user_id), visible_to))
        self._connection.commit()

    def read(self, limit=-1):
        sql = """select message, user_id, visible_to, id
            from chat
            order by timestamp desc
            limit (?)"""

        result = self._execute(sql, (limit,)).fetchall()

        return [self._to_message(r) for r in result][::-1]

    def read_latest(self, pk):
        sql = """select message, user_id, visible_to, id
            from chat
            where id > (?)
            order by timestamp desc
            """

        result = self._execute(sql, (pk,)).fetchall()

        return [self._to_message(r) for r in result][::-1]

    def remove_bot_messages_for(self, user):
        sql = """delete from chat
            where user_id = (?) and visible_to like (?);
        """

        alfabot_id = str(Users().alfabot().user_id)
        user_id = str(user.user_id)

        self._execute(sql, (alfabot_id, user_id,))

    def delete_latest_message_of(self, user):
        sql = """delete from chat where user_id = (?)
            order by timestamp desc limit 1
        """

        self._execute(sql, (str(user.user_id),))

    def _to_message(self, record):
        message_text = record[0]
        user = Users().find_by_user_id(record[1])
        pk = record[3]

        if not record[2]:
            visible_to = []
        else:
            visible_to = [Users().find_by_user_id(
                id) for id in record[2].split(",")]

        return Message(message_text, user, visible_to, pk)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.close()
