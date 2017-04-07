#!/usr/bin/env python3
from models import Users

for user in Users().all():
    print("{0}\t\t{1}".format(user.username, user.user_id))
