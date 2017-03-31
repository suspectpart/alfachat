import sqlite3

from uuid import UUID

PATH = "chat.sqlite"


class User(object):

    def __init__(self, username, color, number, uuid):
        self.username = username
        self.color = color
        self.number = number
        self.user_id = uuid

    def exists(self):
        with sqlite3.connect(PATH) as connection:
            User._initialize_database(connection)

            sql = """select exists(select 1 from users where user_id=(?) LIMIT 1)
            """
            result = connection.cursor().execute(sql, (str(self.user_id),))
            return bool(result.fetchone()[0])

    def save(self):
        with sqlite3.connect(PATH) as connection:
            User._initialize_database(connection)

            sql = """insert into users
                (name, user_id, color, number)
                values (?, ?, ?, ?)
            """

            try:
                connection.cursor().execute(
                    sql, (self.username, str(self.user_id), self.color, self.number))
                connection.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def _execute(self, sql, params):
        return self._connection.cursor().execute(sql, params)

    @staticmethod
    def _initialize_database(connection):
        sql = """create table if not exists users (
            id integer primary key not null,
            name text not null,
            user_id text not null unique,
            color text not null,
            number text
        )"""

        connection.cursor().execute(sql, ())
        connection.commit()

    @staticmethod
    def find_by_name(name):
        with sqlite3.connect(PATH) as connection:
            User._initialize_database(connection)

            sql = """select * from users where name=(?)
            """

            result = connection.cursor().execute(sql, (name,))
            record = result.fetchone()

            if record:
                return User(record[1], record[3], record[4], UUID(record[2]))

            return None

    @staticmethod
    def find_by_user_id(uuid_str):
        with sqlite3.connect(PATH) as connection:
            User._initialize_database(connection)

            sql = """select * from users where user_id=(?)
            """

            result = connection.cursor().execute(sql, (uuid_str,))
            record = result.fetchone()

            if record:
                return User(record[1], record[3], record[4], UUID(record[2]))

            return None

    @staticmethod
    def all():
        with sqlite3.connect(PATH) as connection:
            User._initialize_database(connection)

            sql = """select * from users"""

            result = connection.cursor().execute(sql, ())

            return [User(r[1], r[3], r[4], UUID(r[2])) for r in result]

    @staticmethod
    def trump():
        return User.find_by_name("trump")

    @staticmethod
    def alfabot():
        return User.find_by_name("alfabot")

    def __str__(self):
        return str(self.user_id)

    def __eq__(self, other):
        return other and (self.user_id == other.user_id)

    __repr__ = __str__


class Message:

    def __init__(self, message_text, user, visible_to=None):
        self.user = user
        self.text = message_text
        self.visible_to = visible_to or []

    def __str__(self):
        return "[{0}] {1} (visible to {2})".format(
            self.user.username,
            self.text, ",".join(map(str, self.visible_to)))


class Chat(object):

    def __init__(self):
        self._connection = sqlite3.connect(PATH)
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

        self._execute(sql, (message.text, str(
            message.user.user_id), visible_to))
        self._connection.commit()

    def read(self, limit=-1):
        sql = """select message, user_id, visible_to
            from chat
            order by timestamp desc
            limit (?)"""

        result = self._execute(sql, (limit,))

        return [self._to_message(r) for r in result][::-1]

    def delete_latest_message_of(self, user):
        sql = """delete from chat where user_id = (?)
            order by timestamp desc limit 1
        """

        self._execute(sql, (str(user.user_id),))

    def _to_message(self, record):
        message_text = record[0]
        user = User.find_by_user_id(record[1])

        if not record[2]:
            visible_to = []
        else:
            visible_to = [User.find_by_user_id(
                id) for id in record[2].split(",")]

        return Message(message_text, user, visible_to)
