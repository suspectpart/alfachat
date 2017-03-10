import sqlite3
import json

PATH = "chat.sqlite"


class Message:

    def __init__(self, message_text, username, visible_to=None):
        self.username = username
        self.text = message_text
        self.visible_to = visible_to or []

    def __str__(self):
        return "[{0}] {1} (visible to {2})".format(self.username, self.text, self.visible_to)


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
            username text not null,
            visible_to text not null,
            timestamp datetime default current_timestamp
        )"""

        self._execute(sql, ())
        self._connection.commit()

    def write(self, message):
        sql = """insert into chat (message, username, visible_to)
            values (?, ?, ?)"""

        message_text = message.text
        username = message.username
        visible_to = json.dumps(message.visible_to)

        self._execute(sql, (message_text, username, visible_to))
        self._connection.commit()

    def read(self):
        sql = """select message, username, visible_to 
            from chat 
            limit 250"""
        for record in self._execute(sql, ()):
            yield Message(record[0], record[1], json.loads(record[2]))


if __name__ == "__main__":
    chat = Chat()
    # chat.clear()
    message = Message("Test", "horst", ["patrick", "horst"])
    chat.write(message)
    messages = chat.read()
    for message in messages:
        print(message)
