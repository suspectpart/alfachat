import config
from uuid import UUID


class User(object):

    def __init__(self, username, color, number, uuid):
        self.username = username
        self.color = color
        self.number = number
        self.uuid = uuid

    def __str__(self):
        return str(self.uuid)

    def __eq__(self, other):
        return self.uuid == other.uuid

    __repr__ = __str__


def find_by_name(name):
    for user_id, values in config.users.items():
        if values[0] == name:
            return User(*values, uuid=user_id)
    return None


def find_by_user_id(uuid_str):
    user_id = UUID(uuid_str)

    try:
        return User(*config.users[user_id], uuid=user_id)
    except:
        return None


def alfabot():
    return find_by_name("alfabot")
