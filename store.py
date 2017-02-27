import sqlite3
import users

PATH = "chat.sqlite"


class Message:

    def __init__(self, message_text, user, visible_to=None):
        self.user = user
        self.text = message_text
        self.visible_to = visible_to or []

    def __str__(self):
        return "[{0}] {1} (visible to {2})".format(self.user.username, self.text,  ",".join(map(str, message.visible_to)))


class Chat(object):

    def __init__(self, path=''):
        self._connection = sqlite3.connect(path or PATH)
        self._initialize_database()

    def clear(self):
        sql = """delete from chat"""
        self._execute(sql, ())

    def close(self):
        self._connection.commit()
        self._connection.close()

    def _execute(self, sql, params):
        return self._connection.cursor().execute(sql, params)

    def _initialize_database(self):
        sql = """create table if not exists chat (
            id integer primary key not null,
            message text not null,
            user_id text not null,
            visible_to text not null,
            timestamp datetime default current_timestamp
        )"""

        self._execute(sql, ())
        self._connection.commit()

    def write(self, message):
        sql = """insert into chat (message, user_id, visible_to)
            values (?, ?, ?)"""

        visible_to = ",".join(map(str, message.visible_to))

        self._execute(sql, (message.text, str(message.user.uuid), visible_to))
        self._connection.commit()

    def read(self):
        sql = """select message, user_id, visible_to 
            from chat 
            limit 250"""

        return [self.message_from_record(r) for r in self._execute(sql, ())]

    def message_from_record(self, record):
        message_text = record[0]
        user = users.find_by_user_id(record[1])

        if not record[2]:
            visible_to = []
        else:
            visible_to = [users.find_by_user_id(
                id) for id in record[2].split(",")]

        return Message(message_text, user, visible_to)
