#!/usr/bin/env python3
import sys
import uuid

from config import users
from models import User

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("corret usage: ./adduser.py <username> <color> [<number>]")
        sys.exit(1)

    username, color = sys.argv[1:3]
    number = sys.argv[3] if len(sys.argv) > 3 else ""
    user_id = uuid.uuid4()

    url = "http://localhorst.duckdns.org:8080/{0}".format(str(user_id))

    user = User(username, color, number, user_id).save()

    print("Added user {0} ({1})".format(username, url))

    sys.exit(0)
