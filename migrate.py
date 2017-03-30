#!/usr/bin/env python3

from config import users
from models import User

if __name__ == "__main__":
    users_migrated = 0

    for user_id, values in users.items():
        user = User(*values, user_id)
        print(user.exists())
        success = user.save()

        users_migrated += int(success)

    print("Migrated {0} users".format(users_migrated))
