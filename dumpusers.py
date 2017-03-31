#!/usr/bin/env python3
from models import User

if __name__ == "__main__":

    for user in User.all():
        print("{0}\t\t{1}".format(user.username, user.user_id))
